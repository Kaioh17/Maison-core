import qrcode 


def subdomain_qrcode(sub_domain):
    """sub_domain: 'https://limo.usmaison.io' """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(sub_domain)
    
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    return img


def custom_qrcode(url: str, fill_color: str = "black", back_color: str = "white"):
    """Generate a QR code with custom URL + colors."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    return qr.make_image(fill_color=fill_color, back_color=back_color)