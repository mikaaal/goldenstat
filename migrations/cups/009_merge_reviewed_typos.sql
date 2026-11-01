-- Players registered more than once in the cups, found by find_cup_typos.py and reviewed one
-- by one: spelling mistakes ("Linus Delby" for "Linus Dellby"), and names that differ only
-- in accents, punctuation or a trophy emoji ("Wille Edgren🏆"). The correct spelling is kept
-- where it can be told, otherwise the one in most cups. Left out on purpose: names where both
-- spellings have league matches of their own (Stefan Jonsson / Stefan Jansson), pairs who played
-- the same cup, initials (Peter L / Peder L), and common names from different clubs
-- (Emil Jonsson / Emil Jansson, Micke Lindberg / Micke Lundberg).

-- Adam Lohlolm -> Adam Loholm
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4384, 158, 'Adam Lohlolm', 'Adam Loholm', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4384 AND name = 'Adam Lohlolm')
  AND EXISTS (SELECT 1 FROM players WHERE id = 158 AND name = 'Adam Loholm');
-- Aleksandr Shelogov -> Aleksandr Shelegov
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4499, 5911, 'Aleksandr Shelogov', 'Aleksandr Shelegov', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4499 AND name = 'Aleksandr Shelogov')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5911 AND name = 'Aleksandr Shelegov');
-- Aleksandr Shelekgov -> Aleksandr Shelegov
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6329, 5911, 'Aleksandr Shelekgov', 'Aleksandr Shelegov', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6329 AND name = 'Aleksandr Shelekgov')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5911 AND name = 'Aleksandr Shelegov');
-- Alexander Georgion -> Alexander Georgiou
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4526, 4200, 'Alexander Georgion', 'Alexander Georgiou', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4526 AND name = 'Alexander Georgion')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4200 AND name = 'Alexander Georgiou');
-- Alexander Gergiou -> Alexander Georgiou
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5353, 4200, 'Alexander Gergiou', 'Alexander Georgiou', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5353 AND name = 'Alexander Gergiou')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4200 AND name = 'Alexander Georgiou');
-- Alexander Wiik -> Alexander Wik
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6856, 5773, 'Alexander Wiik', 'Alexander Wik', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6856 AND name = 'Alexander Wiik')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5773 AND name = 'Alexander Wik');
-- André Ullstand-Olsson -> André Ullstrand-Olsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4874, 4152, 'André Ullstand-Olsson', 'André Ullstrand-Olsson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4874 AND name = 'André Ullstand-Olsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4152 AND name = 'André Ullstrand-Olsson');
-- Anggoon Thiratraiphip -> Anggoon Thiratraithip
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4245, 1688, 'Anggoon Thiratraiphip', 'Anggoon Thiratraithip', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4245 AND name = 'Anggoon Thiratraiphip')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1688 AND name = 'Anggoon Thiratraithip');
-- Anneli Angberg -> Annelie Angberg
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4018, 58, 'Anneli Angberg', 'Annelie Angberg', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4018 AND name = 'Anneli Angberg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 58 AND name = 'Annelie Angberg');
-- Annica Bernegård -> Annica Bernergård
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5128, 2011, 'Annica Bernegård', 'Annica Bernergård', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5128 AND name = 'Annica Bernegård')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2011 AND name = 'Annica Bernergård');
-- Annicka Lingvall -> Annika Lingvall
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4007, 3280, 'Annicka Lingvall', 'Annika Lingvall', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4007 AND name = 'Annicka Lingvall')
  AND EXISTS (SELECT 1 FROM players WHERE id = 3280 AND name = 'Annika Lingvall');
-- Ari Navalainen -> Ari Nevalainen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7164, 1476, 'Ari Navalainen', 'Ari Nevalainen', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7164 AND name = 'Ari Navalainen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1476 AND name = 'Ari Nevalainen');
-- Bat-Ulzii Ganbold -> Batulzii Ganbold
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6491, 4699, 'Bat-Ulzii Ganbold', 'Batulzii Ganbold', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6491 AND name = 'Bat-Ulzii Ganbold')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4699 AND name = 'Batulzii Ganbold');
-- Benjamin Baerentssen -> Benjamin Baerentsen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7023, 5491, 'Benjamin Baerentssen', 'Benjamin Baerentsen', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7023 AND name = 'Benjamin Baerentssen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5491 AND name = 'Benjamin Baerentsen');
-- Benjamin Baerentesen -> Benjamin Baerentsen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6906, 5491, 'Benjamin Baerentesen', 'Benjamin Baerentsen', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6906 AND name = 'Benjamin Baerentesen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5491 AND name = 'Benjamin Baerentsen');
-- Billy Sjöwall -> Billy Sjövall
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5066, 224, 'Billy Sjöwall', 'Billy Sjövall', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5066 AND name = 'Billy Sjöwall')
  AND EXISTS (SELECT 1 FROM players WHERE id = 224 AND name = 'Billy Sjövall');
-- Björn Flod -> Björn Flood
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4656, 1282, 'Björn Flod', 'Björn Flood', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4656 AND name = 'Björn Flod')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1282 AND name = 'Björn Flood');
-- Careen Thue -> Careen True
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6835, 187, 'Careen Thue', 'Careen True', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6835 AND name = 'Careen Thue')
  AND EXISTS (SELECT 1 FROM players WHERE id = 187 AND name = 'Careen True');
-- Carina Nordh Carlstad Dart Club -> Carina Nord Carlstad Dart Club
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6936, 6792, 'Carina Nordh Carlstad Dart Club', 'Carina Nord Carlstad Dart Club', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6936 AND name = 'Carina Nordh Carlstad Dart Club')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6792 AND name = 'Carina Nord Carlstad Dart Club');
-- Carola Sandquist -> Carola Sandqvist
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6400, 5799, 'Carola Sandquist', 'Carola Sandqvist', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6400 AND name = 'Carola Sandquist')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5799 AND name = 'Carola Sandqvist');
-- Cecila Liepe -> Cecilia Liepe
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 1000, 4638, 'Cecila Liepe', 'Cecilia Liepe', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1000 AND name = 'Cecila Liepe')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4638 AND name = 'Cecilia Liepe');
-- Chris Calinan -> Chris Callinan
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5354, 4435, 'Chris Calinan', 'Chris Callinan', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5354 AND name = 'Chris Calinan')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4435 AND name = 'Chris Callinan');
-- Christer Daglberg -> Christer Dahlberg
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4166, 1313, 'Christer Daglberg', 'Christer Dahlberg', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4166 AND name = 'Christer Daglberg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1313 AND name = 'Christer Dahlberg');
-- Chrstian Johnsson -> Christian Johnsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4207, 3977, 'Chrstian Johnsson', 'Christian Johnsson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4207 AND name = 'Chrstian Johnsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 3977 AND name = 'Christian Johnsson');
-- Chrstian Sätterström -> Christian Sätterström
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4908, 621, 'Chrstian Sätterström', 'Christian Sätterström', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4908 AND name = 'Chrstian Sätterström')
  AND EXISTS (SELECT 1 FROM players WHERE id = 621 AND name = 'Christian Sätterström');
-- Christoffer Linqvist -> Christoffer Lindqvist
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6857, 6567, 'Christoffer Linqvist', 'Christoffer Lindqvist', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6857 AND name = 'Christoffer Linqvist')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6567 AND name = 'Christoffer Lindqvist');
-- Daniel Happala Brudin -> Daniel Happala Brundin
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4640, 98, 'Daniel Happala Brudin', 'Daniel Happala Brundin', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4640 AND name = 'Daniel Happala Brudin')
  AND EXISTS (SELECT 1 FROM players WHERE id = 98 AND name = 'Daniel Happala Brundin');
-- Daniel Klöfhorn -> Daniel Klöfkorn
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4692, 1689, 'Daniel Klöfhorn', 'Daniel Klöfkorn', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4692 AND name = 'Daniel Klöfhorn')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1689 AND name = 'Daniel Klöfkorn');
-- Dave Overal -> Dave Overall
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6681, 3776, 'Dave Overal', 'Dave Overall', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6681 AND name = 'Dave Overal')
  AND EXISTS (SELECT 1 FROM players WHERE id = 3776 AND name = 'Dave Overall');
-- David Thorpe -> David Thorp
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6354, 4700, 'David Thorpe', 'David Thorp', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6354 AND name = 'David Thorpe')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4700 AND name = 'David Thorp');
-- Dennis Eriksson Gungner Ds -> Dennis Eriksson Gugner Ds
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6717, 6233, 'Dennis Eriksson Gungner Ds', 'Dennis Eriksson Gugner Ds', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6717 AND name = 'Dennis Eriksson Gungner Ds')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6233 AND name = 'Dennis Eriksson Gugner Ds');
-- Dennis Lippponen -> Dennis Lipponen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6470, 6495, 'Dennis Lippponen', 'Dennis Lipponen', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6470 AND name = 'Dennis Lippponen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6495 AND name = 'Dennis Lipponen');
-- Diego Fosshaug Correia -> Diogo Fosshaug Correia
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 2639, 5046, 'Diego Fosshaug Correia', 'Diogo Fosshaug Correia', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 2639 AND name = 'Diego Fosshaug Correia')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5046 AND name = 'Diogo Fosshaug Correia');
-- Ebbot Remesaho Willnert -> Ebbot Remesaho Willner
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4130, 693, 'Ebbot Remesaho Willnert', 'Ebbot Remesaho Willner', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4130 AND name = 'Ebbot Remesaho Willnert')
  AND EXISTS (SELECT 1 FROM players WHERE id = 693 AND name = 'Ebbot Remesaho Willner');
-- Edvin Silvernagel -> Edvin Silfvernagel
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6907, 6840, 'Edvin Silvernagel', 'Edvin Silfvernagel', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6907 AND name = 'Edvin Silvernagel')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6840 AND name = 'Edvin Silfvernagel');
-- Edvin Nutti -> Edwin Nutti
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5161, 5378, 'Edvin Nutti', 'Edwin Nutti', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5161 AND name = 'Edvin Nutti')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5378 AND name = 'Edwin Nutti');
-- Eliott Kjelleryd -> Elliot Kjelleryd
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4470, 4377, 'Eliott Kjelleryd', 'Elliot Kjelleryd', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4470 AND name = 'Eliott Kjelleryd')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4377 AND name = 'Elliot Kjelleryd');
-- Elliott Kjelleryd -> Elliot Kjelleryd
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4212, 4377, 'Elliott Kjelleryd', 'Elliot Kjelleryd', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4212 AND name = 'Elliott Kjelleryd')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4377 AND name = 'Elliot Kjelleryd');
-- Elliot Kjellryd -> Elliot Kjelleryd
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4194, 4377, 'Elliot Kjellryd', 'Elliot Kjelleryd', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4194 AND name = 'Elliot Kjellryd')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4377 AND name = 'Elliot Kjelleryd');
-- Elliott Kjellryd -> Elliot Kjelleryd
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4188, 4377, 'Elliott Kjellryd', 'Elliot Kjelleryd', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4188 AND name = 'Elliott Kjellryd')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4377 AND name = 'Elliot Kjelleryd');
-- Emelie Tjärnström -> Emelie Tjernström
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6659, 6828, 'Emelie Tjärnström', 'Emelie Tjernström', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6659 AND name = 'Emelie Tjärnström')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6828 AND name = 'Emelie Tjernström');
-- Erik Pihl -> Eric Pihl
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6623, 5525, 'Erik Pihl', 'Eric Pihl', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6623 AND name = 'Erik Pihl')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5525 AND name = 'Eric Pihl');
-- Fredrik Almqvist -> Fredrik Almquist
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4734, 5366, 'Fredrik Almqvist', 'Fredrik Almquist', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4734 AND name = 'Fredrik Almqvist')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5366 AND name = 'Fredrik Almquist');
-- Fredrik Gurgensen -> Fredrik Görgensen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4406, 481, 'Fredrik Gurgensen', 'Fredrik Görgensen', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4406 AND name = 'Fredrik Gurgensen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 481 AND name = 'Fredrik Görgensen');
-- Fredrik Jonassson -> Fredrik Jonasson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6474, 6494, 'Fredrik Jonassson', 'Fredrik Jonasson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6474 AND name = 'Fredrik Jonassson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6494 AND name = 'Fredrik Jonasson');
-- Fredric Lingvall -> Fredrik Lingvall
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4006, 1692, 'Fredric Lingvall', 'Fredrik Lingvall', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4006 AND name = 'Fredric Lingvall')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1692 AND name = 'Fredrik Lingvall');
-- Fredrika Thor -> Fredrika Thour
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4459, 764, 'Fredrika Thor', 'Fredrika Thour', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4459 AND name = 'Fredrika Thor')
  AND EXISTS (SELECT 1 FROM players WHERE id = 764 AND name = 'Fredrika Thour');
-- Frida Persdotrter -> Frida Persdotter
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4863, 180, 'Frida Persdotrter', 'Frida Persdotter', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4863 AND name = 'Frida Persdotrter')
  AND EXISTS (SELECT 1 FROM players WHERE id = 180 AND name = 'Frida Persdotter');
-- Gatis Grandberg -> Gatis Grandbergs
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4061, 48, 'Gatis Grandberg', 'Gatis Grandbergs', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4061 AND name = 'Gatis Grandberg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 48 AND name = 'Gatis Grandbergs');
-- Jesper Kjellson -> Jesper Kjellsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 1508, 5072, 'Jesper Kjellson', 'Jesper Kjellsson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1508 AND name = 'Jesper Kjellson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5072 AND name = 'Jesper Kjellsson');
-- Jimmie Torn`eus -> Jimmie Torneus
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6273, 4749, 'Jimmie Torn`eus', 'Jimmie Torneus', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6273 AND name = 'Jimmie Torn`eus')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4749 AND name = 'Jimmie Torneus');
-- Johan Linderberg -> Johan Lindeberg
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4252, 309, 'Johan Linderberg', 'Johan Lindeberg', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4252 AND name = 'Johan Linderberg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 309 AND name = 'Johan Lindeberg');
-- Johan Lindesberg -> Johan Lindeberg
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6322, 309, 'Johan Lindesberg', 'Johan Lindeberg', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6322 AND name = 'Johan Lindesberg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 309 AND name = 'Johan Lindeberg');
-- Jonni Klemetti -> Joni Klemetti
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4422, 4514, 'Jonni Klemetti', 'Joni Klemetti', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4422 AND name = 'Jonni Klemetti')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4514 AND name = 'Joni Klemetti');
-- Jonu Klemetti -> Joni Klemetti
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4147, 4514, 'Jonu Klemetti', 'Joni Klemetti', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4147 AND name = 'Jonu Klemetti')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4514 AND name = 'Joni Klemetti');
-- Jonas Zallin -> Jonas Zahlin
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7158, 782, 'Jonas Zallin', 'Jonas Zahlin', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7158 AND name = 'Jonas Zallin')
  AND EXISTS (SELECT 1 FROM players WHERE id = 782 AND name = 'Jonas Zahlin');
-- Karl Berström -> Karl Bergström
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5160, 4757, 'Karl Berström', 'Karl Bergström', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5160 AND name = 'Karl Berström')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4757 AND name = 'Karl Bergström');
-- Kenth Kjellbom -> Kent Kjellbom
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4639, 1009, 'Kenth Kjellbom', 'Kent Kjellbom', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4639 AND name = 'Kenth Kjellbom')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1009 AND name = 'Kent Kjellbom');
-- Kent Meldstedt -> Kent Mellstedt
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6170, 5318, 'Kent Meldstedt', 'Kent Mellstedt', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6170 AND name = 'Kent Meldstedt')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5318 AND name = 'Kent Mellstedt');
-- Kentha Ohlsson -> Kentha Olsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 3857, 1008, 'Kentha Ohlsson', 'Kentha Olsson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 3857 AND name = 'Kentha Ohlsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1008 AND name = 'Kentha Olsson');
-- Kavin Fors -> Kevin Fors
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6324, 5639, 'Kavin Fors', 'Kevin Fors', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6324 AND name = 'Kavin Fors')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5639 AND name = 'Kevin Fors');
-- Kim Fogerberg -> Kim Fagerberg
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4614, 4477, 'Kim Fogerberg', 'Kim Fagerberg', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4614 AND name = 'Kim Fogerberg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4477 AND name = 'Kim Fagerberg');
-- Kjelle Hverven -> Kjell Hverven
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4870, 5123, 'Kjelle Hverven', 'Kjell Hverven', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4870 AND name = 'Kjelle Hverven')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5123 AND name = 'Kjell Hverven');
-- Krister Papaioanou -> Krister Papaioannou
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6514, 72, 'Krister Papaioanou', 'Krister Papaioannou', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6514 AND name = 'Krister Papaioanou')
  AND EXISTS (SELECT 1 FROM players WHERE id = 72 AND name = 'Krister Papaioannou');
-- Ktister Papaioannou -> Krister Papaioannou
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4864, 72, 'Ktister Papaioannou', 'Krister Papaioannou', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4864 AND name = 'Ktister Papaioannou')
  AND EXISTS (SELECT 1 FROM players WHERE id = 72 AND name = 'Krister Papaioannou');
-- Kristoffer Axén -> Kristofer Axén
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 3639, 6572, 'Kristoffer Axén', 'Kristofer Axén', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 3639 AND name = 'Kristoffer Axén')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6572 AND name = 'Kristofer Axén');
-- Kristoffer Browall -> Kristofer Browall
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6001, 5364, 'Kristoffer Browall', 'Kristofer Browall', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6001 AND name = 'Kristoffer Browall')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5364 AND name = 'Kristofer Browall');
-- Kristoffer Björ -> Kristoffer Björk
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6140, 3415, 'Kristoffer Björ', 'Kristoffer Björk', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6140 AND name = 'Kristoffer Björ')
  AND EXISTS (SELECT 1 FROM players WHERE id = 3415 AND name = 'Kristoffer Björk');
-- Kristoffer Heiersson -> Kristoffer Heierson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4363, 2644, 'Kristoffer Heiersson', 'Kristoffer Heierson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4363 AND name = 'Kristoffer Heiersson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2644 AND name = 'Kristoffer Heierson');
-- Kristoffer Spets -> Kristoffer Spetz
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4664, 475, 'Kristoffer Spets', 'Kristoffer Spetz', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4664 AND name = 'Kristoffer Spets')
  AND EXISTS (SELECT 1 FROM players WHERE id = 475 AND name = 'Kristoffer Spetz');
-- Lars Anderssson -> Lars Andersson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4082, 430, 'Lars Anderssson', 'Lars Andersson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4082 AND name = 'Lars Anderssson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 430 AND name = 'Lars Andersson');
-- Larsa Jansson -> Lars Jansson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4062, 234, 'Larsa Jansson', 'Lars Jansson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4062 AND name = 'Larsa Jansson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 234 AND name = 'Lars Jansson');
-- Lee Hensall -> Lee Henshall
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4246, 3957, 'Lee Hensall', 'Lee Henshall', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4246 AND name = 'Lee Hensall')
  AND EXISTS (SELECT 1 FROM players WHERE id = 3957 AND name = 'Lee Henshall');
-- Leif Koronen -> Leif Korhonen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4315, 95, 'Leif Koronen', 'Leif Korhonen', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4315 AND name = 'Leif Koronen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 95 AND name = 'Leif Korhonen');
-- Lennarts Ericsson -> Lennart Ericsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6618, 5394, 'Lennarts Ericsson', 'Lennart Ericsson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6618 AND name = 'Lennarts Ericsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5394 AND name = 'Lennart Ericsson');
-- Linus Delby -> Linus Dellby
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7157, 144, 'Linus Delby', 'Linus Dellby', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7157 AND name = 'Linus Delby')
  AND EXISTS (SELECT 1 FROM players WHERE id = 144 AND name = 'Linus Dellby');
-- Linus Lunddroth -> Linus Lundroth
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4659, 168, 'Linus Lunddroth', 'Linus Lundroth', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4659 AND name = 'Linus Lunddroth')
  AND EXISTS (SELECT 1 FROM players WHERE id = 168 AND name = 'Linus Lundroth');
-- Louis Magnusson-Palm -> Louise Magnusson-Palm
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4523, 1087, 'Louis Magnusson-Palm', 'Louise Magnusson-Palm', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4523 AND name = 'Louis Magnusson-Palm')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1087 AND name = 'Louise Magnusson-Palm');
-- Lukas Le Hegerat -> Lukas Le Hegarat
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4657, 276, 'Lukas Le Hegerat', 'Lukas Le Hegarat', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4657 AND name = 'Lukas Le Hegerat')
  AND EXISTS (SELECT 1 FROM players WHERE id = 276 AND name = 'Lukas Le Hegarat');
-- Magnus Aaronsson -> Magnus Aronsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6668, 5154, 'Magnus Aaronsson', 'Magnus Aronsson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6668 AND name = 'Magnus Aaronsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5154 AND name = 'Magnus Aronsson');
-- Maik Gustavsson -> Maik Gustafsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4830, 4346, 'Maik Gustavsson', 'Maik Gustafsson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4830 AND name = 'Maik Gustavsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4346 AND name = 'Maik Gustafsson');
-- Manage Hämäläinen -> Mange Hämäläinen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5800, 6126, 'Manage Hämäläinen', 'Mange Hämäläinen', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5800 AND name = 'Manage Hämäläinen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6126 AND name = 'Mange Hämäläinen');
-- Marcus Elfors -> Marcus Elffors
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4405, 614, 'Marcus Elfors', 'Marcus Elffors', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4405 AND name = 'Marcus Elfors')
  AND EXISTS (SELECT 1 FROM players WHERE id = 614 AND name = 'Marcus Elffors');
-- Markus Lehtonen -> Marcus Lehtonen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4421, 4145, 'Markus Lehtonen', 'Marcus Lehtonen', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4421 AND name = 'Markus Lehtonen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4145 AND name = 'Marcus Lehtonen');
-- Markus Reher -> Marcus Reher
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4316, 1286, 'Markus Reher', 'Marcus Reher', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4316 AND name = 'Markus Reher')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1286 AND name = 'Marcus Reher');
-- Marko Bibic -> Marko Bilic
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6814, 5175, 'Marko Bibic', 'Marko Bilic', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6814 AND name = 'Marko Bibic')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5175 AND name = 'Marko Bilic');
-- Marco Bilic -> Marko Bilic
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6319, 5175, 'Marco Bilic', 'Marko Bilic', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6319 AND name = 'Marco Bilic')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5175 AND name = 'Marko Bilic');
-- Martin Pattersson-Sjöö -> Martin Pettersson-Sjö
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4189, 7062, 'Martin Pattersson-Sjöö', 'Martin Pettersson-Sjö', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4189 AND name = 'Martin Pattersson-Sjöö')
  AND EXISTS (SELECT 1 FROM players WHERE id = 7062 AND name = 'Martin Pettersson-Sjö');
-- Mattias Milterius -> Mathias Milterius
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5171, 5317, 'Mattias Milterius', 'Mathias Milterius', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5171 AND name = 'Mattias Milterius')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5317 AND name = 'Mathias Milterius');
-- Max Hansen Lööf -> Max Hansen Löf
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5150, 4668, 'Max Hansen Lööf', 'Max Hansen Löf', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5150 AND name = 'Max Hansen Lööf')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4668 AND name = 'Max Hansen Löf');
-- Melinda Sjölin -> Melinda Sjödin
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6516, 6468, 'Melinda Sjölin', 'Melinda Sjödin', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6516 AND name = 'Melinda Sjölin')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6468 AND name = 'Melinda Sjödin');
-- Micael Bohman -> Mikael Bohman
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4345, 5618, 'Micael Bohman', 'Mikael Bohman', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4345 AND name = 'Micael Bohman')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5618 AND name = 'Mikael Bohman');
-- Micael Sundin -> Michael Sundin
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6747, 6267, 'Micael Sundin', 'Michael Sundin', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6747 AND name = 'Micael Sundin')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6267 AND name = 'Michael Sundin');
-- Michaela Räisenen -> Michaela Räisänen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5169, 5315, 'Michaela Räisenen', 'Michaela Räisänen', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5169 AND name = 'Michaela Räisenen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5315 AND name = 'Michaela Räisänen');
-- Mickael Forsberg -> Mikael Forsberg
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6917, 6450, 'Mickael Forsberg', 'Mikael Forsberg', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6917 AND name = 'Mickael Forsberg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6450 AND name = 'Mikael Forsberg');
-- Mikael Jadenborg -> Mikael Jedenborg
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4549, 540, 'Mikael Jadenborg', 'Mikael Jedenborg', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4549 AND name = 'Mikael Jadenborg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 540 AND name = 'Mikael Jedenborg');
-- Mickael Jedenborg -> Mikael Jedenborg
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4860, 540, 'Mickael Jedenborg', 'Mikael Jedenborg', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4860 AND name = 'Mickael Jedenborg')
  AND EXISTS (SELECT 1 FROM players WHERE id = 540 AND name = 'Mikael Jedenborg');
-- Nnan Tipjuta -> Nan Tipjuta
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7033, 5634, 'Nnan Tipjuta', 'Nan Tipjuta', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7033 AND name = 'Nnan Tipjuta')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5634 AND name = 'Nan Tipjuta');
-- Nettan Rickardsson -> Nettan Richardson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4261, 4258, 'Nettan Rickardsson', 'Nettan Richardson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4261 AND name = 'Nettan Rickardsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4258 AND name = 'Nettan Richardson');
-- Niklas Lindmark -> Nicklas Lindmark
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4314, 3976, 'Niklas Lindmark', 'Nicklas Lindmark', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4314 AND name = 'Niklas Lindmark')
  AND EXISTS (SELECT 1 FROM players WHERE id = 3976 AND name = 'Nicklas Lindmark');
-- Nicklas Dahlgren -> Niklas Dahlgren
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4776, 997, 'Nicklas Dahlgren', 'Niklas Dahlgren', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4776 AND name = 'Nicklas Dahlgren')
  AND EXISTS (SELECT 1 FROM players WHERE id = 997 AND name = 'Niklas Dahlgren');
-- Noah Mattson -> Noah Mattsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5526, 4670, 'Noah Mattson', 'Noah Mattsson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5526 AND name = 'Noah Mattson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4670 AND name = 'Noah Mattsson');
-- Oscar Faults -> Oscar Faulds
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4513, 4608, 'Oscar Faults', 'Oscar Faulds', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4513 AND name = 'Oscar Faults')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4608 AND name = 'Oscar Faulds');
-- Oskar Faulds -> Oscar Faulds
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4585, 4608, 'Oskar Faulds', 'Oscar Faulds', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4585 AND name = 'Oskar Faulds')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4608 AND name = 'Oscar Faulds');
-- Oskar Axelsson -> Oskar Axelson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6884, 5147, 'Oskar Axelsson', 'Oskar Axelson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6884 AND name = 'Oskar Axelsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5147 AND name = 'Oskar Axelson');
-- Otgon Byanbaa -> Otgon Byambaa
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4230, 1098, 'Otgon Byanbaa', 'Otgon Byambaa', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4230 AND name = 'Otgon Byanbaa')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1098 AND name = 'Otgon Byambaa');
-- Otgon Byamba -> Otgon Byambaa
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5878, 1098, 'Otgon Byamba', 'Otgon Byambaa', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5878 AND name = 'Otgon Byamba')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1098 AND name = 'Otgon Byambaa');
-- Patrik Malmèn -> Patrik Malmen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6817, 865, 'Patrik Malmèn', 'Patrik Malmen', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6817 AND name = 'Patrik Malmèn')
  AND EXISTS (SELECT 1 FROM players WHERE id = 865 AND name = 'Patrik Malmen');
-- Percy Mikaelsson -> Percy Mickelsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7063, 156, 'Percy Mikaelsson', 'Percy Mickelsson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7063 AND name = 'Percy Mikaelsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 156 AND name = 'Percy Mickelsson');
-- Peter Erson -> Peter Ersson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4043, 40, 'Peter Erson', 'Peter Ersson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4043 AND name = 'Peter Erson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 40 AND name = 'Peter Ersson');
-- Peter Fogelkvist -> Peter Fogelqvist
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4619, 2624, 'Peter Fogelkvist', 'Peter Fogelqvist', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4619 AND name = 'Peter Fogelkvist')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2624 AND name = 'Peter Fogelqvist');
-- peter Polkajärvi -> Peter Poikajärvi
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 3007, 4174, 'peter Polkajärvi', 'Peter Poikajärvi', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 3007 AND name = 'peter Polkajärvi')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4174 AND name = 'Peter Poikajärvi');
-- Petra Elfstöm -> Petra Elfström
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7156, 377, 'Petra Elfstöm', 'Petra Elfström', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7156 AND name = 'Petra Elfstöm')
  AND EXISTS (SELECT 1 FROM players WHERE id = 377 AND name = 'Petra Elfström');
-- Pia Airisnemi -> Pia Airisniemi
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4542, 1779, 'Pia Airisnemi', 'Pia Airisniemi', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4542 AND name = 'Pia Airisnemi')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1779 AND name = 'Pia Airisniemi');
-- Pontus Guldenstam -> Pontus Guldestam
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 1680, 5801, 'Pontus Guldenstam', 'Pontus Guldestam', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 1680 AND name = 'Pontus Guldenstam')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5801 AND name = 'Pontus Guldestam');
-- Rasmus Jacobsson -> Rasmus Jakobsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6860, 6908, 'Rasmus Jacobsson', 'Rasmus Jakobsson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6860 AND name = 'Rasmus Jacobsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6908 AND name = 'Rasmus Jakobsson');
-- Rymond Hansson -> Raymond Hansson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6524, 101, 'Rymond Hansson', 'Raymond Hansson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6524 AND name = 'Rymond Hansson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 101 AND name = 'Raymond Hansson');
-- Richard Duner -> Richard Dunér
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7149, 3020, 'Richard Duner', 'Richard Dunér', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7149 AND name = 'Richard Duner')
  AND EXISTS (SELECT 1 FROM players WHERE id = 3020 AND name = 'Richard Dunér');
-- Rikard Roy -> Rickard Roy
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6663, 580, 'Rikard Roy', 'Rickard Roy', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6663 AND name = 'Rikard Roy')
  AND EXISTS (SELECT 1 FROM players WHERE id = 580 AND name = 'Rickard Roy');
-- Rickard Siverts -> Rickard Sieverts
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4613, 217, 'Rickard Siverts', 'Rickard Sieverts', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4613 AND name = 'Rickard Siverts')
  AND EXISTS (SELECT 1 FROM players WHERE id = 217 AND name = 'Rickard Sieverts');
-- Robert Kalisczak -> Robert Kaliszczak
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4827, 959, 'Robert Kalisczak', 'Robert Kaliszczak', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4827 AND name = 'Robert Kalisczak')
  AND EXISTS (SELECT 1 FROM players WHERE id = 959 AND name = 'Robert Kaliszczak');
-- Robert Södertvall -> Robert Södervall
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4866, 190, 'Robert Södertvall', 'Robert Södervall', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4866 AND name = 'Robert Södertvall')
  AND EXISTS (SELECT 1 FROM players WHERE id = 190 AND name = 'Robert Södervall');
-- Råger Ångbäck -> Roger Ångbäck
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6684, 6455, 'Råger Ångbäck', 'Roger Ångbäck', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6684 AND name = 'Råger Ångbäck')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6455 AND name = 'Roger Ångbäck');
-- Ronjia Nilsson -> Ronja Nilsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5694, 5475, 'Ronjia Nilsson', 'Ronja Nilsson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5694 AND name = 'Ronjia Nilsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5475 AND name = 'Ronja Nilsson');
-- Ronny Drammen -> Ronny Dammen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5481, 5640, 'Ronny Drammen', 'Ronny Dammen', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5481 AND name = 'Ronny Drammen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5640 AND name = 'Ronny Dammen');
-- Sabastian Dahl -> Sebastian Dahl
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6257, 6757, 'Sabastian Dahl', 'Sebastian Dahl', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6257 AND name = 'Sabastian Dahl')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6757 AND name = 'Sebastian Dahl');
-- Sami Heikkanen -> Sami Heikkinen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4081, 1082, 'Sami Heikkanen', 'Sami Heikkinen', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4081 AND name = 'Sami Heikkanen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1082 AND name = 'Sami Heikkinen');
-- Sami Heikinen -> Sami Heikkinen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6563, 1082, 'Sami Heikinen', 'Sami Heikkinen', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6563 AND name = 'Sami Heikinen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 1082 AND name = 'Sami Heikkinen');
-- Sebastian Paillante -> Sebastian Pailante
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6454, 6107, 'Sebastian Paillante', 'Sebastian Pailante', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6454 AND name = 'Sebastian Paillante')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6107 AND name = 'Sebastian Pailante');
-- Sigge Yilitalo -> Sigge Ylitalo
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5852, 5632, 'Sigge Yilitalo', 'Sigge Ylitalo', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5852 AND name = 'Sigge Yilitalo')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5632 AND name = 'Sigge Ylitalo');
-- Sigge Yitalo Pieti -> Sigge Ylitalo Pieti
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6569, 5473, 'Sigge Yitalo Pieti', 'Sigge Ylitalo Pieti', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6569 AND name = 'Sigge Yitalo Pieti')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5473 AND name = 'Sigge Ylitalo Pieti');
-- Stefan Lundwall -> Stefan Lundvall
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6861, 5872, 'Stefan Lundwall', 'Stefan Lundvall', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6861 AND name = 'Stefan Lundwall')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5872 AND name = 'Stefan Lundvall');
-- Stefan Norberger -> Stefan Noberger
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5702, 5176, 'Stefan Norberger', 'Stefan Noberger', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5702 AND name = 'Stefan Norberger')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5176 AND name = 'Stefan Noberger');
-- Stefan Norbergwr -> Stefan Noberger
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6338, 5176, 'Stefan Norbergwr', 'Stefan Noberger', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6338 AND name = 'Stefan Norbergwr')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5176 AND name = 'Stefan Noberger');
-- Stybbe Stridh -> Stybbe Strid
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5763, 5493, 'Stybbe Stridh', 'Stybbe Strid', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5763 AND name = 'Stybbe Stridh')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5493 AND name = 'Stybbe Strid');
-- Theo Widemark -> Teo Widemark
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4531, 4382, 'Theo Widemark', 'Teo Widemark', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4531 AND name = 'Theo Widemark')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4382 AND name = 'Teo Widemark');
-- Teo Lundblad -> Theo Lundblad
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4604, 668, 'Teo Lundblad', 'Theo Lundblad', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4604 AND name = 'Teo Lundblad')
  AND EXISTS (SELECT 1 FROM players WHERE id = 668 AND name = 'Theo Lundblad');
-- Thomas Glanz -> Thomas Glantz
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5740, 5910, 'Thomas Glanz', 'Thomas Glantz', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5740 AND name = 'Thomas Glanz')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5910 AND name = 'Thomas Glantz');
-- Tomas Magnusson -> Thomas Magnusson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6045, 5381, 'Tomas Magnusson', 'Thomas Magnusson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6045 AND name = 'Tomas Magnusson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5381 AND name = 'Thomas Magnusson');
-- Tomas Vedestig -> Thomas Vedestig
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6682, 6673, 'Tomas Vedestig', 'Thomas Vedestig', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6682 AND name = 'Tomas Vedestig')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6673 AND name = 'Thomas Vedestig');
-- Tobias Petersson -> Tobias Pettersson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7124, 5165, 'Tobias Petersson', 'Tobias Pettersson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7124 AND name = 'Tobias Petersson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5165 AND name = 'Tobias Pettersson');
-- Thomas Wahlström -> Tomas Wahlström
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6834, 863, 'Thomas Wahlström', 'Tomas Wahlström', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6834 AND name = 'Thomas Wahlström')
  AND EXISTS (SELECT 1 FROM players WHERE id = 863 AND name = 'Tomas Wahlström');
-- Tommy Erntson -> Tommy Erntzon
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 5963, 6758, 'Tommy Erntson', 'Tommy Erntzon', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 5963 AND name = 'Tommy Erntson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6758 AND name = 'Tommy Erntzon');
-- Tony Baron -> Tony Barouni
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4550, 3937, 'Tony Baron', 'Tony Barouni', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4550 AND name = 'Tony Baron')
  AND EXISTS (SELECT 1 FROM players WHERE id = 3937 AND name = 'Tony Barouni');
-- Tony Baroni -> Tony Barouni
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4525, 3937, 'Tony Baroni', 'Tony Barouni', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4525 AND name = 'Tony Baroni')
  AND EXISTS (SELECT 1 FROM players WHERE id = 3937 AND name = 'Tony Barouni');
-- Viktor Berman -> Viktor Bergman
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7022, 6859, 'Viktor Berman', 'Viktor Bergman', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7022 AND name = 'Viktor Berman')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6859 AND name = 'Viktor Bergman');
-- Viktor Kosic -> Viktor Kostic
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4131, 4138, 'Viktor Kosic', 'Viktor Kostic', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4131 AND name = 'Viktor Kosic')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4138 AND name = 'Viktor Kostic');
-- Vilda Jansson -> Vilda Jonsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6024, 5928, 'Vilda Jansson', 'Vilda Jonsson', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6024 AND name = 'Vilda Jansson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5928 AND name = 'Vilda Jonsson');
-- Wille Cedskog -> Wille Cedeskog
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 3530, 3989, 'Wille Cedskog', 'Wille Cedeskog', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 3530 AND name = 'Wille Cedskog')
  AND EXISTS (SELECT 1 FROM players WHERE id = 3989 AND name = 'Wille Cedeskog');
-- Willam Einerfeldt -> William Einerfeldt
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4518, 145, 'Willam Einerfeldt', 'William Einerfeldt', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4518 AND name = 'Willam Einerfeldt')
  AND EXISTS (SELECT 1 FROM players WHERE id = 145 AND name = 'William Einerfeldt');
-- Åsa Schöntal -> Åsa Schönthal
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4344, 2667, 'Åsa Schöntal', 'Åsa Schönthal', 'typo'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4344 AND name = 'Åsa Schöntal')
  AND EXISTS (SELECT 1 FROM players WHERE id = 2667 AND name = 'Åsa Schönthal');
-- Andrè Johannessen -> Andre Johannessen
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6743, 6266, 'Andrè Johannessen', 'Andre Johannessen', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6743 AND name = 'Andrè Johannessen')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6266 AND name = 'Andre Johannessen');
-- Andrè Johannessen Motala Dc -> Andre Johannessen Motala Dc
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6707, 6226, 'Andrè Johannessen Motala Dc', 'Andre Johannessen Motala Dc', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6707 AND name = 'Andrè Johannessen Motala Dc')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6226 AND name = 'Andre Johannessen Motala Dc');
-- Kjell Norden -> Kjell Nordén
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6741, 240, 'Kjell Norden', 'Kjell Nordén', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6741 AND name = 'Kjell Norden')
  AND EXISTS (SELECT 1 FROM players WHERE id = 240 AND name = 'Kjell Nordén');
-- Linn Hällström Larsson -> Linn Hällström-Larsson
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6646, 992, 'Linn Hällström Larsson', 'Linn Hällström-Larsson', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6646 AND name = 'Linn Hällström Larsson')
  AND EXISTS (SELECT 1 FROM players WHERE id = 992 AND name = 'Linn Hällström-Larsson');
-- Peter W. Cannermo -> Peter W Cannermo
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7151, 999, 'Peter W. Cannermo', 'Peter W Cannermo', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7151 AND name = 'Peter W. Cannermo')
  AND EXISTS (SELECT 1 FROM players WHERE id = 999 AND name = 'Peter W Cannermo');
-- Alex Akaslompolo -> Alex Äkäslompolo
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 4534, 6949, 'Alex Akaslompolo', 'Alex Äkäslompolo', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 4534 AND name = 'Alex Akaslompolo')
  AND EXISTS (SELECT 1 FROM players WHERE id = 6949 AND name = 'Alex Äkäslompolo');
-- Max Hansen-Löf -> Max Hansen Löf
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7025, 4668, 'Max Hansen-Löf', 'Max Hansen Löf', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7025 AND name = 'Max Hansen-Löf')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4668 AND name = 'Max Hansen Löf');
-- Dennis Sandhu🏆 -> Dennis Sandhu
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 7209, 4728, 'Dennis Sandhu🏆', 'Dennis Sandhu', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 7209 AND name = 'Dennis Sandhu🏆')
  AND EXISTS (SELECT 1 FROM players WHERE id = 4728 AND name = 'Dennis Sandhu');
-- Wille Edgren🏆 -> Wille Edgren
INSERT OR IGNORE INTO cup_player_mappings (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
SELECT 6985, 5312, 'Wille Edgren🏆', 'Wille Edgren', 'name_variant'
WHERE EXISTS (SELECT 1 FROM players WHERE id = 6985 AND name = 'Wille Edgren🏆')
  AND EXISTS (SELECT 1 FROM players WHERE id = 5312 AND name = 'Wille Edgren');

-- As in 008: point aliases of aliases at the final player and move the links over.

UPDATE cup_player_mappings
SET canonical_player_id = (SELECT b.canonical_player_id FROM cup_player_mappings b
                           WHERE b.alias_player_id = cup_player_mappings.canonical_player_id),
    canonical_name = (SELECT b.canonical_name FROM cup_player_mappings b
                      WHERE b.alias_player_id = cup_player_mappings.canonical_player_id)
WHERE canonical_player_id IN (SELECT alias_player_id FROM cup_player_mappings)
  AND canonical_player_id != alias_player_id;

UPDATE cup_player_mappings
SET canonical_player_id = (SELECT b.canonical_player_id FROM cup_player_mappings b
                           WHERE b.alias_player_id = cup_player_mappings.canonical_player_id),
    canonical_name = (SELECT b.canonical_name FROM cup_player_mappings b
                      WHERE b.alias_player_id = cup_player_mappings.canonical_player_id)
WHERE canonical_player_id IN (SELECT alias_player_id FROM cup_player_mappings)
  AND canonical_player_id != alias_player_id;

UPDATE cup_player_mappings
SET canonical_player_id = (SELECT b.canonical_player_id FROM cup_player_mappings b
                           WHERE b.alias_player_id = cup_player_mappings.canonical_player_id),
    canonical_name = (SELECT b.canonical_name FROM cup_player_mappings b
                      WHERE b.alias_player_id = cup_player_mappings.canonical_player_id)
WHERE canonical_player_id IN (SELECT alias_player_id FROM cup_player_mappings)
  AND canonical_player_id != alias_player_id;

UPDATE cup_player_mappings
SET canonical_player_id = (SELECT b.canonical_player_id FROM cup_player_mappings b
                           WHERE b.alias_player_id = cup_player_mappings.canonical_player_id),
    canonical_name = (SELECT b.canonical_name FROM cup_player_mappings b
                      WHERE b.alias_player_id = cup_player_mappings.canonical_player_id)
WHERE canonical_player_id IN (SELECT alias_player_id FROM cup_player_mappings)
  AND canonical_player_id != alias_player_id;

-- canonical_name is shown in match lists, so keep it equal to the player's current name
UPDATE cup_player_mappings
SET canonical_name = (SELECT name FROM players WHERE id = cup_player_mappings.canonical_player_id)
WHERE canonical_name != (SELECT name FROM players WHERE id = cup_player_mappings.canonical_player_id);

-- Only some queries look at cup_player_mappings, so links still on an alias move to the
-- final player, as review_typos.py does. A pair already linked to both keeps one link.
DELETE FROM participant_players
WHERE player_id IN (SELECT alias_player_id FROM cup_player_mappings)
  AND EXISTS (
      SELECT 1 FROM participant_players pp
      JOIN cup_player_mappings m ON m.canonical_player_id = pp.player_id
      WHERE m.alias_player_id = participant_players.player_id
        AND pp.participant_id = participant_players.participant_id
  );

UPDATE participant_players
SET player_id = (SELECT canonical_player_id FROM cup_player_mappings
                 WHERE alias_player_id = participant_players.player_id)
WHERE player_id IN (SELECT alias_player_id FROM cup_player_mappings);
