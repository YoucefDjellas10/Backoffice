{
    "name": "Reservation Demo",
    "depends": ["base", "dom_gantt_view_time_scale"],
    "summary": "Car rental",
    "data": [
        "demo/car_model_demo_data.xml",
        "demo/cars_demo_data.xml",
        "demo/reservation_demo_data.xml",
        # "security/ir.model.access.csv",
        "views/reservation_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "reservation_demo/static/src/**/*",
        ],
    },
    "application": True,
}
