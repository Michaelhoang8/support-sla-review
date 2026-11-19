SELECT d.team,t.age_band,COUNT(*) open_tickets,SUM(overdue_open) overdue FROM tickets t JOIN teams d USING(team_id) WHERE t.open_flag=1 GROUP BY d.team,t.age_band ORDER BY d.team,t.age_band
