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