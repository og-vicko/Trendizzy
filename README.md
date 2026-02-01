# Trendizzy
Creating the first AI trend decision making personal assistant application.


### Design Decision
* Initially attempted pytrends, but migrated to trends.py due to maintenance and compatibility issues. This reduced dependency risk and improved pipeline stability
* Google Trends ingestion uses trendspy. Returned objects are normalized into primitive JSON-safe types at the ingestion boundary to keep raw storage simple and debuggable.