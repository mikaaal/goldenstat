"""
Adresser till n01:s API.

Värdnamnet finns bara här. n01 har bytt värdnamn tidigare (oktober 2026
slutade certifikatet gälla för tk2-228-23746.vs.sakura.ne.jp), så vid nästa
byte räcker det att ändra N01_HOST.

lb är lastbalanseraren som n01:s egen sajt använder. Peka inte på servrarna
bakom den (t.ex. lb2), de kan flyttas eller byta namn.
"""

N01_HOST = 'lb.n01darts.com'

TOURNAMENT_BASE = f'https://{N01_HOST}/n01/tournament'
TOURNAMENT_API = f'{TOURNAMENT_BASE}/n01_tournament.php'
LEAGUE_API = f'https://{N01_HOST}/n01/league/n01_league.php'
MATCH_DATA_URL = f'{TOURNAMENT_BASE}/n01_online_t.php?cmd=get_setdata&tmid='


def match_url(tmid: str) -> str:
    """URL för en matchs data utifrån dess tmid"""
    return MATCH_DATA_URL + tmid


def tmid_from_url(url: str) -> str:
    """Plocka ut tmid ur en match-URL. Värden utan 'tmid=' returneras oförändrade."""
    return url.split('tmid=', 1)[1] if 'tmid=' in url else url


def mirrored_tmid(tmid: str) -> str:
    """Samma match med lagen i omvänd ordning (..._lg_0_<kod>_<lagA>_<lagB>)"""
    parts = tmid.rsplit('_', 2)
    if len(parts) != 3:
        return tmid
    return f'{parts[0]}_{parts[2]}_{parts[1]}'
