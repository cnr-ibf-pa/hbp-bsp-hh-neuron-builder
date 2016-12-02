import os

if 'HBPDEV' not in os.environ:
    import hbp_app_python_auth.settings as auth_settings

    auth_settings.SOCIAL_AUTH_HBP_KEY = '0643409b-f9e5-4b05-8f46-0b3e98294631'
    auth_settings.SOCIAL_AUTH_HBP_SECRET = 'AKWvSUNdprd7JpVF73RRFlIgxnUMTUzoImWt5i3T-Q39fZRfFsuaCS0_y6DnNcfsNKm8gEBbdt-jWWC42PwMdZw'
    SECRET_KEY = '7hkbhf66!cj48u0&8d%@_3q@9-@x1(#dpe^(z7l(xe@*%)^^aj'
