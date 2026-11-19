SELECT month,COUNT(*) tickets,SUM(response_eligible) eligible,SUM(response_breach) breaches,1.0-SUM(response_breach)*1.0/SUM(response_eligible) attainment FROM tickets GROUP BY month ORDER BY month
