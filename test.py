# test.py

def test(image, model_dir=None, device_id=0):
    """
    Dummy anti-spoofing test function.
    
    Args:
        image: The image frame (numpy array).
        model_dir: Path to the anti-spoofing models (not used here).
        device_id: Device ID for GPU/CPU (not used here).
        
    Returns:
        1 for real face, 0 for spoof (always returns 1 for now).
    """
    # TODO: Replace this with actual anti-spoofing logic
    return 1
