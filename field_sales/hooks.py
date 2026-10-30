app_name = "field_sales"
app_title = "Field Sales"
app_publisher = "Field Sales Contributors"
app_description = "Field sales and secondary sales management for ERPNext"
app_email = "sunasaramohammadali9@gmail.com"
app_license = "mit"
required_apps = ["erpnext"]

after_install = "field_sales.setup.after_install"
after_migrate = "field_sales.setup.after_migrate"
before_uninstall = "field_sales.setup.before_uninstall"

doc_events = {
	"Sales Order": {
		"before_validate": "field_sales.overrides.sales_order.before_validate",
	},
}

scheduler_events = {
	"hourly": ["field_sales.tasks.auto_close_open_visits"],
}
