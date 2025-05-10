# -*- coding: utf-8 -*-
#################################################################################
# Author      : CFIS (<https://www.cfis.store/>)
# Copyright(c): 2017-Present CFIS.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.cfis.store/>
#################################################################################

{
    "name": "All in One Gantt View | Gantt View",
    "summary": " The Planning view gives you a clear overview of what is already planned and what remains to be planned using Start Date and End Date.",
    "version": "17.1",
    "description": """
        Project Gantt View
        ==================
        This addon allows the users to show projects stasks in  gantt view, in a
        simple and graphical way.
        - Gantt View
        - create new Task
        - customize an existing Tasks
        - TreeView for Gantt Items
        - Task Deadline Indicator
        - Task Priority Indicator
        - Task Progress Indicator
        - Multiple Scales
        - Navigate to Todat, Previous and Next Day
        - Grouping Task/Project
        - Filter
        - Progress bar on Task
        - Popup Task Informations
        - Overdue Indicator
        - Milestone Task in Different Shape
        - Predecessor Links
        - Todyas Marker
        - Sorting
        - Gantt View
        - Project Gantt
        - Project Gantt View
        - Gantt view Project
        - production gantt view
        - Task gantt view 
        - Sale order gantt view
        - purchase gantt view, 
        - stock picking gantt view.
    """,    
    "author": "CFIS",
    "maintainer": "CFIS",
    "license" :  "Other proprietary",
    "website": "https://www.cfis.store",
    "images": ["images/web_gantt_compact_view.png"],
    "category": "Project",
    "depends": [
        "base",
        "web",
        "project",
        "hr",
        "hr_holidays",
        "mrp",
        "sale_management",
        "reservation"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/project_gantt_views.xml",
        "views/hr_holidays_gantt_view.xml",
        "views/mrp_gantt_views.xml",
        "views/sale_gantt_views.xml",
        "views/reservation_gantt.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/web_gantt_compact_view/static/lib/dhtmlxGantt/sources/dhtmlxgantt.css",
            "/web_gantt_compact_view/static/lib/dhtmlxGantt/sources/dhtmlxgantt.js",
            "/web_gantt_compact_view/static/lib/dhtmlxGantt/sources/api.js",
            "/web_gantt_compact_view/static/src/css/*.*",
            "/web_gantt_compact_view/static/src/js/*.*",
        ],
    },
    "installable": True,
    "application": True,
    "price"                :  45,
    "currency"             :  "EUR",
    "uninstall_hook": "uninstall_hook",
}
