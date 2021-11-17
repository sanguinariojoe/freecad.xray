import requests

try:
    from BeautifulSoup import BeautifulSoup as bs
except ImportError:
    from bs4 import BeautifulSoup as bs


DENSITIES_URL = "https://periodictableguide.com/density-of-elements-chart/"
MASS_ATTENUATION_COEFFS_URL = "https://physics.nist.gov/PhysRefData/XrayMassCoef/ElemTab/z{:02d}.html"
ZMAX = 92


def densities_table(html):
    tab = html.body.find('table').find('tbody')
    data = []
    for tr in tab.find_all('tr'):
        td = tr.find_all('td')[-1]
        if td.find('div'):
            td.find('div').clear()
        field, units = td.text.strip().split(" ")
        try:
            dens = float(field)
            if units.lower() == 'g/L':
                dens /= 1000
        except ValueError:
            dens = None
        data.append(dens)
    return data


def mass_coeff_table(html):
    main_div = html.body.find('div', attrs={'align':'center'})
    main_tab = main_div.find('table')
    tab = main_tab.find('table')
    trs = tab.find_all('tr')
    name = trs[0].find('b').text
    name = name[:name.find('\n')]
    data = []
    for tr in trs[5:]:
        row = []
        for td in tr.find_all('td'):
            try:
                row.append(float(td.text))
            except ValueError:
                continue
        data.append(row)
    return name, data


if __name__ == "__main__":
    resp = requests.get(DENSITIES_URL)
    if not resp.ok:
        print("Cannot fetch {}".format(DENSITIES_URL))
        raise IOError
    densities = densities_table(bs(resp.text))

    elements = []
    for z in range(1, ZMAX + 1):
        if densities[z] is None:
            continue
        resp = requests.get(MASS_ATTENUATION_COEFFS_URL.format(z))
        if not resp.ok:
            print("Cannot fetch {}".format(MASS_ATTENUATION_COEFFS_URL.format(z)))
            break
        name, data = mass_coeff_table(bs(resp.text))
        elements.append([name, z, densities[z]])

        # Save the attenutions table
        with open('z{:02d}.csv'.format(z), 'w') as f:
            f.write('"energy [MeV]", "mu [cm2/g]", "mu_en [cm2/g]"\n')
            for elem in data:
                f.write('{},{},{}\n'.format(elem[0], elem[1], elem[2]))


    # Save the elements table
    with open('elements.csv', 'w') as f:
        f.write('"Name", "Z", "dens [g/cm3]"\n')
        for elem in elements:
            f.write('"{}",{},{}\n'.format(elem[0], elem[1], elem[2]))
