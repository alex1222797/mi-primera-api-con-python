import qrcode
dato = "https://share.google/ep8bSX8AVm7VgBKTH"
qr =qrcode.make(dato)
qr.save("escaneame.png")