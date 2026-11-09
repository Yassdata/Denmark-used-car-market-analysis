-- I divide current stock by the recent daily sales pace for the same selection.
WITH filtered AS (
    SELECT makename, modelname, active_inventory, sold_last_45d
    FROM vehicles
    WHERE (:makename IS NULL OR makename = :makename)
      AND (:modelname IS NULL OR modelname = :modelname)
      AND (:fueltype IS NULL OR fueltype = :fueltype)
      AND (:transmissiontype IS NULL OR transmissiontype = :transmissiontype)
      AND (:min_mileage IS NULL OR odometerkm >= :min_mileage)
      AND (:max_mileage IS NULL OR odometerkm <= :max_mileage)
), totals AS (
    SELECT 'overall' AS scope, NULL AS makename, NULL AS modelname,
           COALESCE(SUM(active_inventory), 0) AS active_inventory,
           COALESCE(SUM(sold_last_45d), 0) AS sold_last_45d
    FROM filtered
    UNION ALL
    SELECT 'brand', makename, NULL, SUM(active_inventory), SUM(sold_last_45d)
    FROM filtered
    GROUP BY makename
    UNION ALL
    SELECT 'model', makename, modelname, SUM(active_inventory), SUM(sold_last_45d)
    FROM filtered
    GROUP BY makename, modelname
)
SELECT *, 1.0 * :lookback_days * active_inventory / NULLIF(sold_last_45d, 0) AS market_days_supply
FROM totals
ORDER BY scope, makename, modelname;
