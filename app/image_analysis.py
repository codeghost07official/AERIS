
import cv2
import numpy as np


def create_image_explanation(brightness, contrast, sharpness, edge_density):
    visibility_concerns = []

    if brightness < 70:
        visibility_concerns.append("the picture is dark")
    elif brightness > 190:
        visibility_concerns.append("the picture is very bright")

    if contrast < 35:
        visibility_concerns.append("some areas blend together")

    if sharpness < 50:
        visibility_concerns.append("small details are hard to see")

    if edge_density < 5:
        outlines = "Few outlines stand out, but this alone is not a warning sign."
    else:
        outlines = "Several outlines are visible for a person to look over."

    if visibility_concerns:
        if len(visibility_concerns) == 1:
            concern_text = visibility_concerns[0]
        elif len(visibility_concerns) == 2:
            concern_text = " and ".join(visibility_concerns)
        else:
            concern_text = (
                f"{', '.join(visibility_concerns[:-1])}, and "
                f"{visibility_concerns[-1]}"
            )
        next_step = (
            f"This picture may be hard to inspect because {concern_text}. "
            "A clearer picture or a closer human review may help someone "
            "check the equipment."
        )
    else:
        next_step = (
            "The picture may be easier to review, but these checks did not "
            "find a clear warning sign about the equipment."
        )

    return (
        "AERIS helps people look for possible spacecraft equipment problems. "
        "These image checks did not identify a specific equipment issue. "
        f"{outlines} {next_step} The checks describe the whole picture; they "
        "cannot tell whether the equipment is normal or faulty, or identify "
        "damage. A person should inspect anything that looks unusual."
    )


def analyze_image(file_path):
    try:
        image = cv2.imread(file_path)

        if image is None:
            raise ValueError(
                "Unable to read the image. Please upload a valid JPG or PNG."
            )

        height, width = image.shape[:2]

        if height < 2 or width < 2:
            raise ValueError("The uploaded image is too small.")

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

        brightness = float(np.mean(gray))

        contrast = float(np.std(gray))

        sharpness = float(
            cv2.Laplacian(
                gray,
                cv2.CV_64F
            ).var()
        )

        edges = cv2.Canny(
            gray,
            100,
            200
        )

        edge_density = float(
            np.count_nonzero(edges) / edges.size * 100
        )

        brightness = round(brightness, 2)
        contrast = round(contrast, 2)
        sharpness = round(sharpness, 2)
        edge_density = round(edge_density, 2)

        if brightness < 70:
            brightness_note = "The image is relatively dark."
        elif brightness > 190:
            brightness_note = "The image is relatively bright."
        else:
            brightness_note = "The image has moderate brightness."

        if contrast < 35:
            contrast_note = "Low contrast between image regions."
        else:
            contrast_note = "Noticeable intensity variation is present."

        if sharpness < 50:
            sharpness_note = "The image may contain limited fine detail."
        else:
            sharpness_note = "The image contains measurable fine detail."

        if edge_density < 5:
            edge_note = "Relatively few prominent edges were detected."
        else:
            edge_note = "Multiple prominent edges were detected."

        summary = (
            f"Analyzed a {width} × {height} image. "
            f"Brightness: {brightness}, contrast: {contrast}, "
            f"sharpness: {sharpness}, and edge density: "
            f"{edge_density}%. "
            f"{brightness_note} {contrast_note}"
        )

        interpretation = (
            f"{brightness_note} "
            f"{contrast_note} "
            f"{sharpness_note} "
            f"{edge_note} "
            "These measurements describe image characteristics "
            "and do not independently establish equipment damage."
        )
        plain_language_explanation = create_image_explanation(
            brightness,
            contrast,
            sharpness,
            edge_density,
        )

        return {
            "success": True,
            "width": width,
            "height": height,
            "brightness": brightness,
            "contrast": contrast,
            "sharpness": sharpness,
            "edge_density": edge_density,
            "brightness_note": brightness_note,
            "contrast_note": contrast_note,
            "sharpness_note": sharpness_note,
            "edge_note": edge_note,
            "interpretation": interpretation,
            "summary": summary,
            "plain_language_explanation": plain_language_explanation,
        }

    except Exception as error:
        raise ValueError(
            f"Image analysis failed: {str(error)}"
        ) from error