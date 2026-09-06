from ultralytics import YOLO


MODEL_PATH = (
    "models/best.pt"
)


model = YOLO(
    MODEL_PATH
)


print(
    "\nModel classes:\n"
)


for class_id, name in (
    model.names.items()
):

    print(
        f"{class_id}: {name}"
    )


required_classes = {
    "person",
    "forklift",
}


available_classes = {
    str(name).lower()
    for name
    in model.names.values()
}


print(
    "\nVisionGuard check:"
)


for required in required_classes:

    if (
        required
        in available_classes
    ):

        print(
            f"✓ {required}"
        )

    else:

        print(
            f"✗ {required} missing"
        )