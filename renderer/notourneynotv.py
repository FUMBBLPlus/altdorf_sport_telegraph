FINISHED = '''[table width=100% bg=#E6DDC7][tr]\
[td width=100px][block=right]\
{date}
{time}\
[/block]\
[/td]\
[td width=534px]\
[table blackborder border2 width=100%]\
[tr bg=#224422 fg=#fff][td colspan=3][block=center]{status}[/block][/td][/tr]\
[tr][td colspan=3][block=center]\
[b]{pairing[title]}[/b]\
[/block][/td][/tr]\
[tr][td width=45%][block=right][url=/p/team?team_id={teams[0][id]}]{teams[0][name]}[/url]
[i]{teams[0][roster][name]}[/i]
[url=/~{teams[0][coach][name]}]{teams[0][coach][shownname]}[/url][/block][/td][td width=10%][block=center]
VS[/block][/td][td width=45%][url=/p/team?team_id={teams[1][id]}]{teams[1][name]}[/url]
[i]{teams[1][roster][name]}[/i]
[url=/~{teams[1][coach][name]}]{teams[1][coach][shownname]}[/url][/td][/tr][/table]\
[block position=relative][block position=absolute top=-16px left=498px][size=8][url=/p/group?op=view&group=11363]AST[/url][/size][/block][/block]
[/td]\
[td]\
[url=/p/match?id={match[id]}]Match Report[/url]
[url=/ffblive.jnlp?replay={match[replayId]}]Replay[/url]\
[/td]\
[/tr][/table]'''


FORFEITED = '''[table width=100% bg=#E6DDC7][tr]\
[td width=100px][block=right]\
{date}
{time}\
[/block]\
[/td]\
[td width=534px]\
[table blackborder border2 width=100%]\
[tr bg=#F40606 fg=#fff][td colspan=3][block=center]{status}[/block][/td][/tr]\
[tr][td colspan=3][block=center]\
[b]{pairing[title]}[/b]\
[/block][/td][/tr]\
[tr][td width=45%][block=right][url=/p/team?team_id={teams[0][id]}]{teams[0][name]}[/url]
[i]{teams[0][roster][name]}[/i]
[url=/~{teams[0][coach][name]}]{teams[0][coach][shownname]}[/url][/block][/td][td width=10%][block=center]
VS[/block][/td][td width=45%][url=/p/team?team_id={teams[1][id]}]{teams[1][name]}[/url]
[i]{teams[1][roster][name]}[/i]
[url=/~{teams[1][coach][name]}]{teams[1][coach][shownname]}[/url][/td][/tr][/table]\
[block position=relative][block position=absolute top=-16px left=498px][size=8][url=/p/group?op=view&group=11363]AST[/url][/size][/block][/block]
[/td]\
[td][/td]\
[/tr][/table]'''


LIVE = '''[table width=100% bg=#E6DDC7][tr]\
[td width=100px][block=right]\
{date}
{time}\
[/block]\
[/td]\
[td width=534px]\
[table blackborder border2 width=100%]\
[tr bg=#2F1E39 fg=#fff][td colspan=3][block=center]{status}[/block][/td][/tr]\
[tr][td colspan=3][block=center]\
[b]{pairing[title]}[/b]\
[/block][/td][/tr]\
[tr][td width=45%][block=right][url=/p/team?team_id={teams[0][id]}]{teams[0][name]}[/url]
[i]{teams[0][roster][name]}[/i]
[url=/~{teams[0][coach][name]}]{teams[0][coach][shownname]}[/url][/block][/td][td width=10%][block=center]
VS[/block][/td][td width=45%][url=/p/team?team_id={teams[1][id]}]{teams[1][name]}[/url]
[i]{teams[1][roster][name]}[/i]
[url=/~{teams[1][coach][name]}]{teams[1][coach][shownname]}[/url][/td][/tr][/table]\
[block position=relative][block position=absolute top=-16px left=498px][size=8][url=/p/group?op=view&group=11363]AST[/url][/size][/block][/block]
[/td]\
[td]\
[url=/ffblive.jnlp?spectate={live[id]}]Spectate[/url]\
[/td]\
[/tr][/table]'''


POSTPONED = '''[table width=100% bg=#E6DDC7][tr]\
[td width=100px][block=right]\
{date}
{time}\
[/block]\
[/td]\
[td width=534px]\
[table blackborder border2 width=100%]\
[tr bg=#A8A833 fg=#fff][td colspan=3][block=center]{status}[/block][/td][/tr]\
[tr][td colspan=3][block=center]\
[b]{pairing[title]}[/b]\
[/block][/td][/tr]\
[tr][td width=45%][block=right][url=/p/team?team_id={teams[0][id]}]{teams[0][name]}[/url]
[i]{teams[0][roster][name]}[/i]
[url=/~{teams[0][coach][name]}]{teams[0][coach][shownname]}[/url][/block][/td][td width=10%][block=center]
VS[/block][/td][td width=45%][url=/p/team?team_id={teams[1][id]}]{teams[1][name]}[/url]
[i]{teams[1][roster][name]}[/i]
[url=/~{teams[1][coach][name]}]{teams[1][coach][shownname]}[/url][/td][/tr][/table]\
[block position=relative][block position=absolute top=-16px left=498px][size=8][url=/p/group?op=view&group=11363]AST[/url][/size][/block][/block]
[/td]\
[td][/td]\
[/tr][/table]'''


def render(namespace):
  status = namespace['status'].upper()
  fstr = globals()[status]
  namespace["time"] = ':'.join(namespace["time"].split(':')[:2])
  return fstr.format(**namespace)

