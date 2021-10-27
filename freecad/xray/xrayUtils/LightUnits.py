from FreeCAD import Units


h = Units.parseQuantity('4.135667696E-15 eV*s')
c = Units.parseQuantity('3E8 m/s')


def is_energy(q):
    return q.Unit.Type == 'Work'


def is_frequency(q):
    return q.Unit.Type == 'Frequency'


def is_wavelength(q):
    return q.Unit.Type == 'Length'


def to_energy(q):
    if is_energy(q):
        return q
    if is_frequency(q):
        return h * q
    if is_wavelength(q):
        return h * c / q


def to_frequency(q):
    if is_energy(q):
        return q / h
    if is_frequency(q):
        return q
    if is_wavelength(q):
        return c / q


def to_wavelength(q):
    if is_energy(q):
        return h * c / q
    if is_frequency(q):
        return c / q
    if is_wavelength(q):
        return q
