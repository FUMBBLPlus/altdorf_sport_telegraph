
import collections
import copy
import datetime
import itertools
import json
import math
import pathlib
import sys

import pytz

import fumbbl_session as S

import helper
import renderer

#rootpath = pathlib.Path('.')  # uncomment for jupyter
rootpath = pathlib.Path(__file__).parent  # uncomment for script

ZONE = 'Europe/Stockholm'
TZ = pytz.timezone(ZONE)
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
WATCHING_NAME = '<font size=8><b>WATCHING</b></font><br/>'
LIVE_NAME = '<font color=red size=6><b>LIVE</b></font><br/>'
MODIFIED_NAME = '<font color=red size=6><b>MODIFIED</b></font><br/>'
POSTPONED_NAME = '<font color=red size=6><b>POSTP</b></font><br/>'
FINISHED_NAME = '<font color=red size=6><b>FINISHED</b></font><br/>'
EXTRA_STRIP = ' ⠀'
AST_GROUP_ID = 11363
DEFAULT_TO = ('<GROUP>', '<TOURNAMENT>',)
DEFAULT_SUBJECT = 'AST Hotline'
MESSAGE_BODY_LIMIT = 50000
POSTPONE_TOLERANCE = datetime.timedelta(seconds=900)  # 15 mins
FINISHED_TOLERANCE = 100

with open(rootpath / 'login.json') as f:
    _login = json.load(f)
S.log_in(**_login)

with open(rootpath / 'settings.json') as f:
    settings = json.load(f)

running_text = S.tournament.get_settings(settings["group_id"], settings["running"])["comment"]
running = json.loads(running_text or 'false')
if not running:
    sys.exit()

watching_text = S.tournament.get_settings(settings["group_id"], settings["watching"])["comment"]
watching = json.loads(watching_text or '[]')
fillers_text = S.tournament.get_settings(settings["group_id"], settings["fillers"])["comment"]
fillers = set(json.loads(fillers_text or '[]'))
live_text = S.tournament.get_settings(settings["group_id"], settings["live"])["comment"]
live = {
        tuple(sorted(team_ids)): TZ.localize(datetime.datetime.strptime(last_time, TIME_FORMAT))
        for team_ids, last_time in json.loads(live_text or '[]')
}
print("live", live)
modified_text = S.tournament.get_settings(settings["group_id"], settings["modified"])["comment"]
modified = {
        int(tournamentId): TZ.localize(datetime.datetime.strptime(timestr, TIME_FORMAT)) for tournamentId, timestr
        in json.loads(modified_text or '{}').items()
}
postponed_text = S.tournament.get_settings(settings["group_id"], settings["postponed"])["comment"]
postponed = set(tuple(sorted(team_ids)) for team_ids in json.loads(postponed_text or '[]'))
print("postponed", postponed)

finished_text = S.tournament.get_settings(settings["group_id"], settings["finished"])["comment"]
finished = set(tuple(sorted(match_ids)) for match_ids in json.loads(finished_text or '[]'))
print("finished", finished)

max_finished = 0


subscribers = {d["coach"] for d in S.group.get_members(AST_GROUP_ID)}
ast_staff = {'SzieberthAdam'}

now = datetime.datetime.now(TZ)

tournament_schedule = helper.keydefaultdict(lambda tournamentId: S.tournament.get_schedule(tournamentId))

group = helper.keydefaultdict(lambda groupId: S.group.get(groupId))

group_tournament = {}
tournament_group = {}
groupIds = set(d["groupId"] for d in watching if "groupId" in d)
print(f'Groups: {"; ".join([str(i) for i in sorted(groupIds)])}')
for groupId in groupIds:
    tournaments_ = {
            int(d2["id"]): d2 for d2 in S.group.get_tournaments(groupId)
            if int(d2["id"]) in modified or d2["status"] == 'In Progress'
    }
    for d in tournaments_.values():
        d['group'] = group[groupId]
    tournamentIds = set(d.get("tournamentId") for d in watching if d.get("groupId") == groupId)
    if None in tournamentIds:
        group_tournament[groupId] = tournaments_
    else:
        group_tournament[groupId] = {tournamentId: d for tournamentId, d in tournaments_.items() if tournamentId in tournamentIds}
    tournament_group.update({tournamentId: groupId for tournamentId in group_tournament[groupId]})
tournamentIds = set(tournamentId for d in group_tournament.values() for tournamentId in d)
inProgressTournamentIds = set(
    tournamentId for d in group_tournament.values() for tournamentId, d2 in d.items()
    if d2["status"] == 'In Progress'
)
print(f'Tournaments In Progress: {"; ".join([str(i) for i in sorted(inProgressTournamentIds)])}')

group_team_coaches = helper.keydefaultdict(lambda groupId: {int(d['id']): d['coach'] for d in S.group.get_members(groupId)})

current_matches = {
        tuple(sorted(d2["id"] for d2 in d["teams"])): d
        for d in S.match.get_current() if d.get('tournament', {}).get('id') in tournamentIds
}
print("current matches", current_matches)
events = {}
for groupId, d in group_tournament.items():
    for tournamentId, d2 in d.items():
        d2['groupId'] = groupId
        schedule = d2['schedule'] = tournament_schedule[tournamentId]
        new_modified = last_modified = modified.get(tournamentId, TZ.localize(datetime.datetime(1001, 1, 1, 0, 0)))
        for pairing in schedule:
            pairing['groupId'] = groupId
            pairing['tournamentId'] = tournamentId
            p_modified = pairing.get('modified')
            if not p_modified:
                continue
            p_modified = TZ.localize(datetime.datetime.strptime(p_modified, TIME_FORMAT))
            team_ids = tuple(sorted(d3["id"] for d3 in pairing["teams"]))
            if set(team_ids) & fillers:
                continue
            if p_modified <= last_modified and team_ids not in live and team_ids not in postponed:
                continue
            if pairing.get('result'):
                match_id = pairing["result"].get('id')
                if match_id and match_id in finished:
                    status = 'REPORTED FINISHED'
                elif match_id:
                    status = 'FINISHED'
                    finished.add(match_id)
                    max_finished = max(max_finished, match_id)
                else:
                    status = 'FORFEITED'
                if team_ids in live:
                    if p_modified < live[team_ids] - POSTPONE_TOLERANCE:
                        # excluce former identical matchups in case of multiple in the same tournament
                        continue
                    else:
                        # live match has been ended
                        del live[team_ids]
            elif team_ids in current_matches and team_ids not in live:
                status = 'LIVE'
            elif team_ids not in current_matches and team_ids in live:
                status = 'POSTPONED'
                trigger_time = live[team_ids] + POSTPONE_TOLERANCE
                print([status, trigger_time, now])  # debug
                if trigger_time <= now:
                    del live[team_ids]
                    postponed.add(team_ids)
                elif now <= live[team_ids]:  # should never happen but if it does it causes an endless loop if unhandled
                    del live[team_ids]
                    continue
                else:
                    continue
            else:
                continue
            if status != 'POSTPONED':
                postponed -= {team_ids}
            pairing['status'] = status
            new_modified = max(new_modified, p_modified)
            events[(p_modified, team_ids)] = pairing
        modified[tournamentId] = new_modified

team = helper.keydefaultdict(S.team.get)

def _tournament_team_coach_gen(tournamentId):
    groupId = tournament_group[tournamentId]
    team_coaches = group_team_coaches[groupId]
    teamIds = {
            team['id'] for pairing in tournament_schedule[tournamentId]
            for team in pairing['teams'] if team['id'] not in fillers
    }
    for teamId in teamIds:
        try:
            yield teamId, team_coaches[teamId]
        except KeyError:
            yield teamId, team[teamId]["coach"]["name"]
tournament_team_coaches = helper.keydefaultdict(lambda tournamentId: {
        teamId: coachName for teamId, coachName in _tournament_team_coach_gen(tournamentId)
})

match = helper.keydefaultdict(lambda match_id: S.match.get_list(match_id)[0])

conversations = collections.defaultdict(list)
conversation_settings = {}
for k in sorted(events):
    event = events[k]
    for w in watching:
        if not w.get('conversationId'):
            continue
        conversationId = w['conversationId']
        this_conversation_settings = conversation_settings.setdefault(conversationId, {})
        for subkey in ('subject', 'to', 'intro'):
            wkey = f'conversation{subkey.title()}'
            if wkey in w:
                if subkey == 'to':
                    this_conversation_settings.setdefault(subkey, []).extend(w[wkey])
                else:
                    this_conversation_settings.setdefault(subkey, w[wkey])
        if w.get('tournamentId') != event["tournamentId"] and w.get('groupId') != event["groupId"]:
            continue
        elif w.get('tournamentId') is not None and w["tournamentId"] != event["tournamentId"]:
            continue
        event2 = copy.deepcopy(event)
        namespace = {'groupId': event["groupId"]}
        namespace["pairing"] = {
                k: v for k, v in event2.items()
                if k in ('position', 'round', 'created', 'modified')
        }
        if namespace["pairing"]["position"] <= 0:
            namespace["pairing"]["title"] = f'ROUND {namespace["pairing"]["round"]}'
        else:
            pairing_title_index = math.floor(math.log(namespace["pairing"]["position"], 2))
            if (0 <= pairing_title_index <= 2):
                namespace["pairing"]["title"] = ('FINAL', 'SEMIFINAL', 'QUARTERFINAL')[pairing_title_index]
            else:
                namespace["pairing"]["title"] = f'ROUND OF {2**(pairing_title_index+1)}'
        namespace["status"] = status = event2["status"]
        if status == 'REPORTED FINISHED':
            continue
        if status == 'POSTPONED':
            namespace["date"] = now.strftime("%Y-%m-%d")
            namespace["time"] = now.strftime("%H:%M:%S")
        else:
            namespace["date"], namespace["time"] = event2["modified"].split()
        team_ids = tuple(sorted(t["id"] for t in event["teams"]))
        winner = event2.get("result", {}).get("winner")
        tournament_data = group_tournament[event["groupId"]][event["tournamentId"]]
        namespace["tournament"] = {'id': tournament_data["id"], 'name': tournament_data["name"]}
        namespace["tournament"]["name"] = w.get('tournamentName') or namespace["tournament"]["name"]
        namespace["tournament"]["name"] = namespace["tournament"]["name"].strip(EXTRA_STRIP)
        if status == 'FINISHED':
            match_id = event2["result"]["id"]
            namespace["match"] = copy.deepcopy(match[match_id])
            match_teams = [namespace["match"]["team1"], namespace["match"]["team2"]]
            del namespace["match"]["team1"]
            del namespace["match"]["team2"]
            for k2 in ('date', 'time'):
                namespace[k2] = namespace["match"][k2]
        elif status == 'LIVE':
            namespace["live"] = copy.deepcopy(current_matches[team_ids])
            del namespace["live"]["tournament"]
            match_teams = namespace["live"]["teams"]
            del namespace["live"]["teams"]
            for t in match_teams:
                t["coach"] = {'name': t["coach"], 'rating': t["rating"]}
                del t["rating"]
                del t["race"]
        namespace["teams"] = [copy.deepcopy(event["teams"][_i]) for _i in range(2)]
        for t in namespace["teams"]:
            t.update({k:v for k,v in copy.deepcopy(team[t["id"]]).items() if k not in ('players',)})
            if status in ('FINISHED', 'LIVE'):
                for t2 in match_teams:
                    if t["id"] == t2["id"]:
                        t.update(t2)
            t["name"] = (w.get('teamName', {}).get(t["name"]) or t["name"]).strip()
            t["name"] = t["name"].strip(EXTRA_STRIP)
            t["coach"]["shownname"] = (w.get('coachName', {}).get(t["coach"]["name"]) or t["coach"]["name"]).strip()
            t["coach"]["shownname"] = t["coach"]["shownname"].strip(EXTRA_STRIP)
            t["roster"]["name"] = (w.get('rosterName', {}).get(t["roster"]["name"]) or t["roster"]["name"]).strip()
            t["roster"]["name"] = t["roster"]["name"].strip(EXTRA_STRIP)
            if str(t["id"]) == winner:
                t["winner"] = True
            else:
                t["winner"] = False
            if str(t["teamValue"]).isdecimal():
                if 10000 <= int(t["teamValue"]):
                    t["teamValue"] = f'{t["teamValue"]//1000}k'
                else:
                    t["teamValue"] = f'{t["teamValue"]}k'
        s = renderer.render(namespace, w.get('renderer'))
        conversations[w['conversationId']].append(s)

for conversationId, conversation_elems in conversations.items():
    this_conversation_settings = conversation_settings[conversationId]
    conversation_watching = [w for w in watching if w.get('conversationId') == conversationId]
    def _message_parts_gen():
        message_parts = []
        for message_part in itertools.chain(reversed(conversation_elems), [this_conversation_settings.get('intro', '')]):
            if MESSAGE_BODY_LIMIT < sum(len(m) for m in message_parts) + len(message_part):
                yield message_parts
                message_parts = []
            message_parts.append(message_part)
        else:
            yield message_parts
    for i, message_parts in enumerate(reversed(list(_message_parts_gen()))):
        message = '\n'.join(message_parts).strip()
        if i == 0:
            saved_to = {'<AST>'} | set(this_conversation_settings.get('to', DEFAULT_TO))
            to = copy.deepcopy(saved_to)
            if '<AST>' in to:
                to.remove('<AST>')
                to |= ast_staff
            if '<SUBSCRIBERS>' in to:
                to.remove('<SUBSCRIBERS>')
                to |= subscribers
            if '<GROUP>' in to:
                groupIds = set(w["groupId"] for w in conversation_watching if w.get('groupId'))
                to.remove('<GROUP>')
                for groupId in groupIds:
                    to |= set(group_team_coaches[groupId].values())
            if '<TOURNAMENT>' in to:
                tournamentIds = set(w["tournamentId"] for w in conversation_watching if w.get('tournamentId'))
                to.remove('<TOURNAMENT>')
                for tournamentId in tournamentIds:
                    to |= set(tournament_team_coaches[tournamentId].values())
            if str(conversationId).isdecimal():
                S.message.invite(conversationId, to)
                S.message.post(conversationId, message)
                pass
            else:
                subject = this_conversation_settings.get('subject')
                if not subject:
                    subject = DEFAULT_SUBJECT
                    watching_names = []
                    for w in conversation_watching:
                        if w.get('tournamentId'):
                            watching_names.append(group_tournament[w["groupId"]][w["tournamentId"]]["name"])
                        elif w.get('groupId'):
                            watching_names.append(group[w["groupId"]]["name"])
                    if watching_names:
                        subject += ' for ' + ', '.join(sorted(watching_names))
                new_conversationId = S.message.new(to, subject, message)
                for w in conversation_watching:
                    w["conversationId"] = new_conversationId
                conversation_settings[new_conversationId] = conversation_settings[conversationId]
                conversationId = new_conversationId
        else:
            S.message.post(conversationId, message)

new_watching_text = json.dumps(
        [d for d in watching if d.get('tournamentId') is None or int(d['tournamentId']) in inProgressTournamentIds],
        indent='\t',
)
directory = pathlib.Path(rootpath / 'watching')
if new_watching_text != watching_text or not directory.exists():
    directory.mkdir(parents=True, exist_ok=True)
    with open(directory/f'watching.{now.strftime("%y%m%d.%H%M")}.json', 'w') as f:
        f.write(new_watching_text)
S.tournament.set_settings_data(
    {'name': WATCHING_NAME, 'comment': new_watching_text},
    settings["group_id"], settings["watching"]
)


for team_ids in current_matches:
    live[team_ids] = now
new_live_text = json.dumps([[list(team_ids), last_time.strftime(TIME_FORMAT)] for team_ids, last_time in live.items()])
directory = pathlib.Path(rootpath / 'live')
if new_live_text != live_text or not directory.exists():
    directory.mkdir(parents=True, exist_ok=True)
    with open(directory/f'live.{now.strftime("%y%m%d.%H%M")}.json', 'w') as f:
        f.write(new_live_text)
S.tournament.set_settings_data(
    {'name': LIVE_NAME, 'comment': new_live_text},
    settings["group_id"], settings["live"]
)


new_postponed_text = json.dumps(list(postponed))
S.tournament.set_settings_data(
    {'name': POSTPONED_NAME, 'comment': new_postponed_text},
    settings["group_id"], settings["postponed"]
)

if max_finished:
    new_finished = sorted(match_id for match_id in finished if max_finished <= match_id + FINISHED_TOLERANCE)
    new_finished_text = json.dumps(new_finished)
    S.tournament.set_settings_data(
        {'name': FINISHED_NAME, 'comment': new_finished_text},
        settings["group_id"], settings["finished"]
    )


new_modified_text = json.dumps({
        str(tournamentId): datetimeobj.strftime(TIME_FORMAT)
        for tournamentId, datetimeobj in sorted(modified.items()) if tournamentId in inProgressTournamentIds
}, indent='\t')
directory = pathlib.Path(rootpath / 'modified')
if new_modified_text != modified_text or not directory.exists():
    directory.mkdir(parents=True, exist_ok=True)
    with open(directory/f'modified.{now.strftime("%y%m%d.%H%M")}.json', 'w') as f:
        f.write(new_modified_text)
S.tournament.set_settings_data(
    {'name': MODIFIED_NAME, 'comment': new_modified_text},
    settings["group_id"], settings["modified"]
)
