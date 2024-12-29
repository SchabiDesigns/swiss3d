
def coords2LV03(lat, lng, **kwargs):
    #Breite φ und die Länge λ. https://de.wikipedia.org/wiki/Schweizer_Landeskoordinaten
    φ = lat*3600
    λ = lng*3600

    #Berechnung der Hilfsgrössen:
    φ_ = (φ - 169028.66) / 10000
    λ_ = (λ - 26782.5) / 10000

    #Berechnung der Meterkoordinaten:
    y = round(200147.07 + 308807.95*φ_ + 3745.25*λ_**2 + 76.63*φ_**2 + 119.79*φ_**3 - 194.56*λ_**2*φ_)
    x = round(600072.37 + 211455.93*λ_ - 10938.51*λ_*φ_ - 0.36*λ_*φ_**2 - 44.54*λ_**3)
    return x,y

def coords2LV95(lat, lng, **kwargs):
    #Breite φ und die Länge λ. https://de.wikipedia.org/wiki/Schweizer_Landeskoordinaten
    #Achtung nicht genau gleich!
    φ = lat*3600
    λ = lng*3600

    #Berechnung der Hilfsgrössen:
    φ_ = (φ - 169028.66) / 10000
    λ_ = (λ - 26782.5) / 10000

    #Berechnung der Meterkoordinaten:
    y = round(200147.07 + 308807.95*φ_ + 3745.25*λ_**2 + 76.63*φ_**2 + 119.79*φ_**3 - 194.56*λ_**2*φ_)+1000000
    x = round(600072.37 + 211455.93*λ_ - 10938.51*λ_*φ_ - 0.36*λ_*φ_**2 - 44.54*λ_**3)+2000000
    return x,y