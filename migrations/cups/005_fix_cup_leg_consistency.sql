-- Rätta cupmatcher där legdatan inte stämmer med resultatet efter 004.
--
-- 1. Ospelade legs. n01 lägger upp nästa leg innan matchen är avgjord. Det
--    har endFlag 0 och inga kast, men importerades med winner_side 1 (eller 2
--    om sidorna vändes). Legs utan kast tas bort i matcher där vunna legs per
--    sida stämmer med resultatet när de inte räknas. Det finns också legs utan
--    kast som n01 räknar som spelade (endFlag 1). Då stämmer resultatet redan
--    med dem medräknade, och matchen rörs inte. Matcher med flera delmatcher
--    (leg_number börjar om på 1) rörs inte heller: där är p1_legs_won ibland
--    vunna set och legdatan går inte att jämföra rakt av.
--
-- 2. Vända sidor som 004 inte kunde se: oavgjorda matcher, matcher med
--    ospelade legs, setmatcher och matcher där n01:s egen legdata inte stämmer
--    med resultatet. rr-matcher sparas en gång per riktning (A_B och B_A) från
--    samma n01-match, så de två raderna ska vara spegelvända. I listan nedan
--    var de två raderna identiska, vilket betyder att den ena är vänd. Vilken
--    det är avgjordes mot n01: statsData.tpid mot p1/p2 och kvarvarande poäng
--    per kast i varje leg. tmid står med så att ett fel id inte kan träffas.
BEGIN;

CREATE TEMP TABLE swap_matches AS
WITH verified(id, tmid) AS (VALUES
    (171, 't_fR8b_7492_rr_2_o9BF_TR3M'),
    (2332, 't_fBKO_8883_rr_0_EcFM_ZfSK'),
    (2373, 't_fBKO_8883_rr_7_lhXz_KJFi'),
    (7282, 't_wnK0_3655_rr_5_rdG4_HPpy'),
    (9077, 't_jZTd_0469_rr_2_fL7O_w1Pw'),
    (13426, 't_NzFk_0986_rr_6_2jmJ_JZbV'),
    (18075, 't_tC70_5441_rr_1_pGlX_gQsA'),
    (20675, 't_kc1E_8041_rr_2_jeC5_d6ig'),
    (21266, 't_3FKF_4094_rr_0_e8ey_8bHY'),
    (22461, 't_6A4R_8281_rr_3_XNOt_j0vJ'),
    (23037, 't_mmKn_7711_rr_4_ZIUC_wEU9'),
    (23043, 't_mmKn_7711_rr_5_Z5eB_FwHi'),
    (24663, 't_XOcC_6125_rr_4_KmXs_0gyS'),
    (24811, 't_JqL4_2295_rr_3_XK2h_18n6'),
    (29802, 't_Zvcp_5880_rr_1_VHy7_eCyp'),
    (29808, 't_Zvcp_5880_rr_2_K9uP_qNCC'),
    (29814, 't_Zvcp_5880_rr_3_ecUp_DXeL'),
    (29820, 't_Zvcp_5880_rr_4_IE3i_1TV8'),
    (29832, 't_Zvcp_5880_rr_6_r1M0_GKqL'),
    (29844, 't_Zvcp_5880_rr_8_p5v9_Dsnq'),
    (29850, 't_Zvcp_5880_rr_9_o7ck_6VxS'),
    (30093, 't_JC2I_9261_rr_2_8RT1_V5Yn'),
    (30099, 't_JC2I_9261_rr_3_Nh37_nfnz'),
    (31464, 't_kPMT_5543_rr_1_OEn5_NtE4'),
    (31470, 't_kPMT_5543_rr_2_lDq7_DKjN'),
    (33350, 't_0Tu2_7489_rr_1_wuP0_NW0c'),
    (35711, 't_bvWa_6785_rr_9_HtBN_654a'),
    (38179, 't_HZjz_6120_rr_2_wRCt_rHY2'),
    (39126, 't_5EpZ_3423_rr_1_UsKp_uWhb'),
    (39681, 't_WVFp_7950_rr_4_os9X_UvnX'),
    (40748, 't_cExS_5885_rr_3_KfKY_Qr0x'),
    (41806, 't_SrtL_9434_rr_0_ToGO_h0MV'),
    (41896, 't_rB1f_0924_rr_0_dSEJ_MmiN'),
    (41898, 't_rB1f_0924_rr_0_Giaw_dSEJ'),
    (41900, 't_rB1f_0924_rr_0_Giaw_MmiN'),
    (41912, 't_rB1f_0924_rr_1_OMfT_UhDk'),
    (42102, 't_CAys_3594_rr_0_6C3J_yR19'),
    (42119, 't_CAys_3594_rr_1_YoyO_T40e'),
    (42124, 't_CAys_3594_rr_1_zHHU_YoyO'),
    (42133, 't_CAys_3594_rr_2_YBVw_TKlm'),
    (42185, 't_CAys_3594_rr_4_Dx4t_aHEB'),
    (42333, 't_kBJa_4435_rr_0_ZNmJ_SdKZ'),
    (42344, 't_kBJa_4435_rr_1_R4nq_K6hK'),
    (42348, 't_kBJa_4435_rr_1_vJ87_K6hK'),
    (42360, 't_kBJa_4435_rr_2_1FBg_pBuZ'),
    (42376, 't_kBJa_4435_rr_4_0ppJ_0vb0'),
    (42740, 't_sJnx_2624_rr_3_xMqG_JOms'),
    (46059, 't_rt2D_3039_rr_2_5b4e_hd0Q'),
    (46706, 't_8t5t_4508_rr_1_JYeJ_7PCu'),
    (47304, 't_7T5a_4539_rr_0_KA81_ad04'),
    (47322, 't_7T5a_4539_rr_2_dbbI_i0e1'),
    (47334, 't_7T5a_4539_rr_3_xHDA_W5MT'),
    (47370, 't_7T5a_4539_rr_6_5qDv_7kMv'),
    (47754, 't_sGqy_9619_rr_1_IuvM_7aLn'),
    (48614, 't_8HyR_9405_rr_1_fNB1_GvXE'),
    (49089, 't_eWgY_2653_rr_1_PihS_leMe'),
    (49343, 't_OiMn_5569_rr_5_bcOD_V00H'),
    (50046, 't_AyCm_3899_rr_2_l9G5_HtGK'),
    (50482, 't_8OeF_1010_rr_3_C2Ga_RQy4'),
    (51289, 't_7lrf_9387_rr_6_pUnV_8WJL'),
    (51672, 't_8U51_8279_rr_5_TYTO_wXxq'),
    (52150, 't_j3Kx_5714_rr_10_2Z9Q_Odfv'),
    (53730, 't_UP62_2362_rr_9_ITvv_XvKV'),
    (55257, 't_qYCw_3102_rr_5_0XFv_kcYY'),
    (58221, 't_0vZi_8119_rr_0_DP0N_x2O7'),
    (58810, 't_8wlU_3704_rr_6_aOpg_3kWJ'),
    (58971, 't_7fSR_7236_rr_3_fC3H_Ya8S'),
    (63282, 't_JTIU_2607_rr_4_C2JK_TyoB'),
    (64192, 't_3fV1_1653_rr_7_JfMD_NeK9'),
    (64418, 't_YWno_8559_rr_8_kVUb_2nzp'),
    (65991, 't_V4Te_1546_rr_3_NzbQ_QMs8'),
    (66369, 't_TqgQ_8891_rr_1_PKbR_Yvx4'),
    (67901, 't_Kimm_9794_rr_0_zLV8_WtRS'),
    (67920, 't_Dzu5_2680_rr_1_z8eP_63VP'),
    (68338, 't_kMn9_5979_rr_4_7Nqa_8hpD'),
    (72462, 't_9Z4W_2406_rr_8_jpy3_XP2Z'),
    (72463, 't_9Z4W_2406_rr_8_jpy3_ir40')
)
SELECT m.id
FROM cup_matches m
JOIN verified v ON v.id = m.id AND v.tmid = m.tmid;

CREATE TEMP TABLE match_legs AS
SELECT l.cup_match_id AS id,
       SUM(l.leg_number = 1) AS parts,
       SUM(l.winner_side = 1) AS raw1,
       SUM(l.winner_side = 2) AS raw2,
       SUM(l.winner_side = 1 AND t.leg_id IS NOT NULL) AS real1,
       SUM(l.winner_side = 2 AND t.leg_id IS NOT NULL) AS real2
FROM legs l
LEFT JOIN (SELECT DISTINCT leg_id FROM throws) t ON t.leg_id = l.id
GROUP BY l.cup_match_id;

-- Resultatet sett från legdatans sidor, alltså omvänt för matcher som vänds
CREATE TEMP TABLE drop_empty_legs AS
SELECT ml.id
FROM match_legs ml
JOIN cup_matches m ON m.id = ml.id
JOIN (
    SELECT id,
           CASE WHEN id IN (SELECT id FROM swap_matches) THEN p2_legs_won ELSE p1_legs_won END AS r1,
           CASE WHEN id IN (SELECT id FROM swap_matches) THEN p1_legs_won ELSE p2_legs_won END AS r2
    FROM cup_matches
) r ON r.id = ml.id
WHERE m.has_detail = 1
  AND m.p1_legs_won != m.p2_legs_won
  AND ml.parts = 1
  AND ml.real1 = r.r1 AND ml.real2 = r.r2
  AND NOT (ml.raw1 = r.r1 AND ml.raw2 = r.r2);

UPDATE throws SET side_number = 3 - side_number
WHERE leg_id IN (
    SELECT id FROM legs WHERE cup_match_id IN (SELECT id FROM swap_matches)
);

-- winner_side 0 och 3 förekommer i äldre data och lämnas som de är
UPDATE legs
SET winner_side = CASE WHEN winner_side IN (1, 2) THEN 3 - winner_side ELSE winner_side END,
    first_side = 3 - first_side
WHERE cup_match_id IN (SELECT id FROM swap_matches);

DELETE FROM legs
WHERE cup_match_id IN (SELECT id FROM drop_empty_legs)
  AND NOT EXISTS (SELECT 1 FROM throws th WHERE th.leg_id = legs.id);

DROP TABLE swap_matches;
DROP TABLE match_legs;
DROP TABLE drop_empty_legs;

COMMIT;
