-- Merge league players registered more than once: the same name on several player ids
-- (the site only shows the first id, so the rest of the matches were missing), or the same
-- name with only accents, hyphens or case differing, e.g. "Oscar Rosen" / "Oscar Rosén".
-- Groups where two ids played for different clubs in the same season may be different
-- people and are left out. The kept name is the one with proper Swedish accents, then the
-- one with most matches; the kept id is the lowest id with that name, which the site uses.

-- Alexander Kallin (2356) -> Alexander Kallin (96)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2356, 96, 'Alexander Kallin', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2356 AND name = 'Alexander Kallin')
  AND EXISTS (SELECT 1 FROM players WHERE id = 96 AND name = 'Alexander Kallin');
-- Alexander Kallin (2441) -> Alexander Kallin (96)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2441, 96, 'Alexander Kallin', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2441 AND name = 'Alexander Kallin')
  AND EXISTS (SELECT 1 FROM players WHERE id = 96 AND name = 'Alexander Kallin');
-- Alexandra Vilen (647) -> Alexandra Vilén (2412)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 647, 2412, 'Alexandra Vilén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 647 AND name = 'Alexandra Vilen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2412 AND name = 'Alexandra Vilén');
-- Anders Axen (942) -> Anders Axén (2418)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 942, 2418, 'Anders Axén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 942 AND name = 'Anders Axen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2418 AND name = 'Anders Axén');
-- Anders Skanberg (1250) -> Anders Skånberg (70)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1250, 70, 'Anders Skånberg', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1250 AND name = 'Anders Skanberg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 70 AND name = 'Anders Skånberg');
-- Andre Borgenvik (1177) -> André Borgenvik (2830)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1177, 2830, 'André Borgenvik', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1177 AND name = 'Andre Borgenvik')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2830 AND name = 'André Borgenvik');
-- Ann Marie Tynys Pettersson (2375) -> Ann-marie Tynys Pettersson (182)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2375, 182, 'Ann-marie Tynys Pettersson', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2375 AND name = 'Ann Marie Tynys Pettersson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 182 AND name = 'Ann-marie Tynys Pettersson');
-- Anna Lena Olsson (1504) -> Anna-lena Olsson (29)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1504, 29, 'Anna-lena Olsson', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1504 AND name = 'Anna Lena Olsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 29 AND name = 'Anna-lena Olsson');
-- Anna-lena Vilen (650) -> Anna-lena Vilén (2410)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 650, 2410, 'Anna-lena Vilén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 650 AND name = 'Anna-lena Vilen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2410 AND name = 'Anna-lena Vilén');
-- Anna-lena Vilèn (2574) -> Anna-lena Vilén (2410)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2574, 2410, 'Anna-lena Vilén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2574 AND name = 'Anna-lena Vilèn')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2410 AND name = 'Anna-lena Vilén');
-- Benjamin Helen (783) -> Benjamin Helén (1272)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 783, 1272, 'Benjamin Helén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 783 AND name = 'Benjamin Helen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1272 AND name = 'Benjamin Helén');
-- Christer Olsen (1343) -> Christer Olsén (2777)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1343, 2777, 'Christer Olsén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1343 AND name = 'Christer Olsen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2777 AND name = 'Christer Olsén');
-- Daniel Carlqvist (2358) -> Daniel Carlqvist (8)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2358, 8, 'Daniel Carlqvist', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2358 AND name = 'Daniel Carlqvist')
  AND EXISTS (SELECT 1 FROM players WHERE id = 8 AND name = 'Daniel Carlqvist');
-- Daniel Carlqvist (2440) -> Daniel Carlqvist (8)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2440, 8, 'Daniel Carlqvist', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2440 AND name = 'Daniel Carlqvist')
  AND EXISTS (SELECT 1 FROM players WHERE id = 8 AND name = 'Daniel Carlqvist');
-- Fredrik Görgensen (1446) -> Fredrik Görgensén (2773)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1446, 2773, 'Fredrik Görgensén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1446 AND name = 'Fredrik Görgensen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2773 AND name = 'Fredrik Görgensén');
-- Henrik Norlen (2983) -> Henrik Norlén (2997)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2983, 2997, 'Henrik Norlén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2983 AND name = 'Henrik Norlen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2997 AND name = 'Henrik Norlén');
-- Henrik Petrén (2345) -> Henrik Petrén (1322)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2345, 1322, 'Henrik Petrén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2345 AND name = 'Henrik Petrén')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1322 AND name = 'Henrik Petrén');
-- Ida Garamvōlgyi (2439) -> Ida Garamvölgyi (1066)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2439, 1066, 'Ida Garamvölgyi', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2439 AND name = 'Ida Garamvōlgyi')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1066 AND name = 'Ida Garamvölgyi');
-- Isak Sewón (1239) -> Isak Sewon (2368)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1239, 2368, 'Isak Sewon', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1239 AND name = 'Isak Sewón')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2368 AND name = 'Isak Sewon');
-- Jan Forssen (1485) -> Jan Forssén (2427)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1485, 2427, 'Jan Forssén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1485 AND name = 'Jan Forssen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2427 AND name = 'Jan Forssén');
-- Jimmy Bjeren (1129) -> Jimmy Bjerén (1516)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1129, 1516, 'Jimmy Bjerén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1129 AND name = 'Jimmy Bjeren')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1516 AND name = 'Jimmy Bjerén');
-- Jimmy Dodzeen (542) -> Jimmy Dodzeén (2513)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 542, 2513, 'Jimmy Dodzeén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 542 AND name = 'Jimmy Dodzeen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2513 AND name = 'Jimmy Dodzeén');
-- Jimmy Dodzeèn (669) -> Jimmy Dodzeén (2513)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 669, 2513, 'Jimmy Dodzeén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 669 AND name = 'Jimmy Dodzeèn')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2513 AND name = 'Jimmy Dodzeén');
-- Jimmy Petren (1421) -> Jimmy Petrén (680)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1421, 680, 'Jimmy Petrén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1421 AND name = 'Jimmy Petren')
  AND EXISTS (SELECT 1 FROM players WHERE id = 680 AND name = 'Jimmy Petrén');
-- Johan Blume (102) -> Johan Blüme (2497)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 102, 2497, 'Johan Blüme', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 102 AND name = 'Johan Blume')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2497 AND name = 'Johan Blüme');
-- Jonas Forsström (2348) -> Jonas Forsström (830)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2348, 830, 'Jonas Forsström', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2348 AND name = 'Jonas Forsström')
  AND EXISTS (SELECT 1 FROM players WHERE id = 830 AND name = 'Jonas Forsström');
-- Jonas Linden (622) -> Jonas Lindén (1767)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 622, 1767, 'Jonas Lindén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 622 AND name = 'Jonas Linden')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1767 AND name = 'Jonas Lindén');
-- Jonathan Lovèn (2545) -> Jonathan Lovén (389)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2545, 389, 'Jonathan Lovén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2545 AND name = 'Jonathan Lovèn')
  AND EXISTS (SELECT 1 FROM players WHERE id = 389 AND name = 'Jonathan Lovén');
-- Konrad Hylten (1835) -> Konrad Hyltén (1614)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1835, 1614, 'Konrad Hyltén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1835 AND name = 'Konrad Hylten')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1614 AND name = 'Konrad Hyltén');
-- Lars Erik Enman (2537) -> Lars-erik Enman (1894)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2537, 1894, 'Lars-erik Enman', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2537 AND name = 'Lars Erik Enman')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1894 AND name = 'Lars-erik Enman');
-- Lars-johan Asplund (2770) -> Lars Johan Asplund (2446)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2770, 2446, 'Lars Johan Asplund', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2770 AND name = 'Lars-johan Asplund')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2446 AND name = 'Lars Johan Asplund');
-- Lars Rosen (633) -> Lars Rosén (1233)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 633, 1233, 'Lars Rosén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 633 AND name = 'Lars Rosen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1233 AND name = 'Lars Rosén');
-- Maria Eugenia Pinzon (1514) -> Maria-eugenia Pinzon (1166)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1514, 1166, 'Maria-eugenia Pinzon', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1514 AND name = 'Maria Eugenia Pinzon')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1166 AND name = 'Maria-eugenia Pinzon');
-- Marianne Wathen-erixon (2542) -> Marianne Wathén Erixon (2877)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2542, 2877, 'Marianne Wathén Erixon', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2542 AND name = 'Marianne Wathen-erixon')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2877 AND name = 'Marianne Wathén Erixon');
-- Matz Ahlström (1243) -> Matz Åhlström (2027)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1243, 2027, 'Matz Åhlström', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1243 AND name = 'Matz Ahlström')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2027 AND name = 'Matz Åhlström');
-- Michael Thuden (526) -> Michael Thudén (2817)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 526, 2817, 'Michael Thudén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 526 AND name = 'Michael Thuden')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2817 AND name = 'Michael Thudén');
-- Miche García (2687) -> Miche Garcia (1230)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2687, 1230, 'Miche Garcia', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2687 AND name = 'Miche García')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1230 AND name = 'Miche Garcia');
-- Micke Häll (2096) -> Micke Häll (352)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2096, 352, 'Micke Häll', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2096 AND name = 'Micke Häll')
  AND EXISTS (SELECT 1 FROM players WHERE id = 352 AND name = 'Micke Häll');
-- Mika Alen (1951) -> Mika Alén (2675)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1951, 2675, 'Mika Alén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1951 AND name = 'Mika Alen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2675 AND name = 'Mika Alén');
-- Mikael Berg (2367) -> Mikael Berg (2328)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2367, 2328, 'Mikael Berg', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2367 AND name = 'Mikael Berg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2328 AND name = 'Mikael Berg');
-- Mikael Frisen (1454) -> Mikael Frisén (2887)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1454, 2887, 'Mikael Frisén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1454 AND name = 'Mikael Frisen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2887 AND name = 'Mikael Frisén');
-- Niklas Norden (1451) -> Niklas Nordén (2943)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1451, 2943, 'Niklas Nordén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1451 AND name = 'Niklas Norden')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2943 AND name = 'Niklas Nordén');
-- Oscar Rosen (1248) -> Oscar Rosén (52)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1248, 52, 'Oscar Rosén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1248 AND name = 'Oscar Rosen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 52 AND name = 'Oscar Rosén');
-- Patrik Malmèn (1490) -> Patrik Malmén (2969)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1490, 2969, 'Patrik Malmén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1490 AND name = 'Patrik Malmèn')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2969 AND name = 'Patrik Malmén');
-- Patrik Malmen (2708) -> Patrik Malmén (2969)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2708, 2969, 'Patrik Malmén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2708 AND name = 'Patrik Malmen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2969 AND name = 'Patrik Malmén');
-- Per Ola Karlsson (2397) -> Per-ola Karlsson (416)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2397, 416, 'Per-ola Karlsson', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2397 AND name = 'Per Ola Karlsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 416 AND name = 'Per-ola Karlsson');
-- Peter Pettersson (2337) -> Peter Pettersson (1053)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2337, 1053, 'Peter Pettersson', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2337 AND name = 'Peter Pettersson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1053 AND name = 'Peter Pettersson');
-- Rickard Orrebrink (2327) -> Rickard Orrebrink (710)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2327, 710, 'Rickard Orrebrink', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2327 AND name = 'Rickard Orrebrink')
  AND EXISTS (SELECT 1 FROM players WHERE id = 710 AND name = 'Rickard Orrebrink');
-- Rickard Orrebrink (2409) -> Rickard Orrebrink (710)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2409, 710, 'Rickard Orrebrink', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2409 AND name = 'Rickard Orrebrink')
  AND EXISTS (SELECT 1 FROM players WHERE id = 710 AND name = 'Rickard Orrebrink');
-- Robert Gunther (761) -> Robert Günther (955)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 761, 955, 'Robert Günther', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 761 AND name = 'Robert Gunther')
  AND EXISTS (SELECT 1 FROM players WHERE id = 955 AND name = 'Robert Günther');
-- Rose-marie (1707) -> Rose Marie (496)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1707, 496, 'Rose Marie', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1707 AND name = 'Rose-marie')
  AND EXISTS (SELECT 1 FROM players WHERE id = 496 AND name = 'Rose Marie');
-- Sarah Rosen (1643) -> Sarah Rosén (372)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1643, 372, 'Sarah Rosén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1643 AND name = 'Sarah Rosen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 372 AND name = 'Sarah Rosén');
-- Stefan Edren (1483) -> Stefan Edrén (2424)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1483, 2424, 'Stefan Edrén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1483 AND name = 'Stefan Edren')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2424 AND name = 'Stefan Edrén');
-- Stefan Jansson (2336) -> Stefan Jansson (286)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2336, 286, 'Stefan Jansson', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2336 AND name = 'Stefan Jansson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 286 AND name = 'Stefan Jansson');
-- Stefan Jansson (2435) -> Stefan Jansson (286)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 2435, 286, 'Stefan Jansson', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2435 AND name = 'Stefan Jansson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 286 AND name = 'Stefan Jansson');
-- Sven Oden (1044) -> Sven Odén (2811)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1044, 2811, 'Sven Odén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1044 AND name = 'Sven Oden')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2811 AND name = 'Sven Odén');
-- Tommy Jonsen (1400) -> Tommy Jonsén (2772)
INSERT OR IGNORE INTO player_aliases (alias_player_id, canonical_player_id, canonical_player_name, notes)
SELECT 1400, 2772, 'Tommy Jonsén', 'Samma spelare registrerad flera gånger'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1400 AND name = 'Tommy Jonsen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2772 AND name = 'Tommy Jonsén');

-- Every alias points straight at a player that is not itself an alias
UPDATE player_aliases
SET canonical_player_id = (SELECT b.canonical_player_id FROM player_aliases b
                           WHERE b.alias_player_id = player_aliases.canonical_player_id),
    canonical_player_name = (SELECT b.canonical_player_name FROM player_aliases b
                             WHERE b.alias_player_id = player_aliases.canonical_player_id)
WHERE canonical_player_id IN (SELECT alias_player_id FROM player_aliases);

-- Sub-match mappings between two ids of the same player say nothing once they are merged,
-- and would break the rule that a mapping goes to another player
DELETE FROM sub_match_player_mappings
WHERE COALESCE((SELECT canonical_player_id FROM player_aliases WHERE alias_player_id = original_player_id), original_player_id)
    = COALESCE((SELECT canonical_player_id FROM player_aliases WHERE alias_player_id = correct_player_id), correct_player_id);

-- Mappings to an alias go to the kept player, by id and by name, since the site matches on the name
UPDATE sub_match_player_mappings
SET correct_player_name = (SELECT canonical_player_name FROM player_aliases WHERE alias_player_id = correct_player_id),
    correct_player_id = (SELECT canonical_player_id FROM player_aliases WHERE alias_player_id = correct_player_id)
WHERE correct_player_id IN (SELECT alias_player_id FROM player_aliases);

-- Mappings from an alias move with its matches, unless the kept player already has one for that sub-match
DELETE FROM sub_match_player_mappings
WHERE original_player_id IN (SELECT alias_player_id FROM player_aliases)
  AND EXISTS (
      SELECT 1 FROM sub_match_player_mappings o
      WHERE o.sub_match_id = sub_match_player_mappings.sub_match_id
        AND o.original_player_id = (SELECT canonical_player_id FROM player_aliases
                                    WHERE alias_player_id = sub_match_player_mappings.original_player_id)
  );

UPDATE sub_match_player_mappings
SET original_player_id = (SELECT canonical_player_id FROM player_aliases WHERE alias_player_id = original_player_id)
WHERE original_player_id IN (SELECT alias_player_id FROM player_aliases);

UPDATE sub_match_participants
SET player_id = (SELECT canonical_player_id FROM player_aliases WHERE alias_player_id = sub_match_participants.player_id)
WHERE player_id IN (SELECT alias_player_id FROM player_aliases);
