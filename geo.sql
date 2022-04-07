sel distinct
	branch_name,
	branch_id,
	product_cluster_name,
	case db_id when 1 then 4 else db_id end as db_id,
	CASE branch_name WHEN 'Москва' THEN 'MS' ELSE cp_code2 end as REG_CODE ,
	CASE branch_name WHEN 'Красноярск' THEN 'Сибирь' ELSE macro_cc_name end macro_cc_name
from prd2_dic_v.branch
where product_cluster_name IS NOT NULL
	AND branch_id IS NOT NULL
	AND branch_name NOT LIKE '%CDMA%'
	AND branch_name NOT LIKE '%MVNO%'
	AND branch_name NOT LIKE '%LTE450%'
	AND product_cluster_name<>'Deferred'