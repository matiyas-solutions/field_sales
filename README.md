# Field Sales

An ERPNext app for sales teams in indirect distribution: GPS-verified field visits, outlet stock audits, competitor activity and scheme tracking, plus the rules that keep orders from the field trustworthy. It is the server side of the Field Sales mobile app.

Requires Frappe and ERPNext v16.

## Install

```sh
bench get-app https://your-git-host/field_sales.git
bench --site your-site install-app field_sales
bench --site your-site migrate
```

## Configure

In the ERPNext desk:

1. Create one **Company** per distributor.
2. Build the **Territory** tree to mirror your hierarchy, for example India > West Zone > Gujarat > Ahmedabad.
3. On each **Customer** (retail outlet), set Territory, Distributor, and latitude and longitude.
4. On each **Item**, optionally set Minimum Outlet Stock. Below it, an audit reports Low.
5. Create **FS Scheme** records.
6. For each **User**, assign one field role and add **User Permissions** for their Territory and Company.
7. Review **FS Settings**.

## Who sees what

| Role | Access |
|---|---|
| Sales Representative | Only documents they created |
| Sales Officer, Area, Regional, Zonal and National Sales Manager | Everything inside their Territory and Company User Permissions, including descendant territories |

Seniority comes from where a user's permission sits in the Territory tree. Field roles get `select`, not `read`, on Account, which ERPNext requires to save an order.

Permissions on standard doctypes are granted once, on install, so later changes in Role Permissions Manager survive a migrate.

## Server rules

| Document | Rule |
|---|---|
| FS Visit | Distance from the outlet and duration are calculated here, and anything the phone sent for them is ignored |
| FS Visit | Check-in time, position and photo cannot be changed after creation |
| FS Visit | A check-in beyond the radius, or from a mock location, is flagged but kept |
| FS Visit | Open visits close automatically after the configured hours, hourly job |
| FS Stock Audit | Status is worked out from the Item's minimum, and Area Sales Managers and Sales Officers covering the outlet get an alert |
| FS Scheme | Dates and discount range are validated |
| Sales Order | On new orders with a `fs_client_id`: the rate comes from the Item Price on the order date, discounts are capped at what the scheme allows, and the scheme must have been running on that date |

Orders are judged on their own date because they can be booked offline and sync days later. A withdrawn scheme rejects the order, and the rep sees the reason on the app's Sync screen.

Orders are not touched after creation, so a distributor can still edit a draft in the desk.

## Mobile app

The app talks to this one through Frappe's core REST API only. Doctype names and fields are the contract between them.

## Tests

```sh
python -m unittest field_sales.tests.test_utils
```

The mobile app's repository holds end-to-end tests that exercise these rules against a live site.

## Uninstall

`bench --site your-site uninstall-app field_sales` removes its doctypes, custom fields and permissions. Sales roles stay, because users hold them.

## License

MIT
