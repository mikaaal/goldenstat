-- Flytta alla deltaganden från Johnny Phil (2453) till Johnny Pihl (881)
UPDATE sub_match_participants SET player_id = 881 WHERE player_id = 2453;
