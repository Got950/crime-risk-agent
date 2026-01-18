from typing import List


def generate_recommendations(score: float) -> List[str]:
    """
    Generate security recommendations based on risk score.
    
    """
    if score > 75:
        # Very high risk - need serious security
        return [
            "Install advanced CCTV with remote monitoring",
            "Deploy regular security patrols",
            "Add smart perimeter lighting",
            "Upgrade fences and gates",
            "Enable controlled access systems"
        ]
    if score > 60:
        # High risk - enhanced security
        return [
            "Install 1080p CCTV cameras",
            "Enable motion-activated lighting",
            "Improve fencing and gate systems"
        ]
    if score > 40:
        # Moderate risk - standard security
        return [
            "Install basic CCTV",
            "Improve door/window locks",
            "Trim shrubs to increase visibility"
        ]
    # Low risk
    return ["Basic home security recommended"]


