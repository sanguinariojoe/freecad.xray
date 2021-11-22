import os
import requests

try:
    from BeautifulSoup import BeautifulSoup as bs
except ImportError:
    from bs4 import BeautifulSoup as bs


MASS_ATTENUATION_COEFFS_PREFIX = "https://physics.nist.gov/PhysRefData/XrayMassCoef/"                 
DENSITIES_URL = MASS_ATTENUATION_COEFFS_PREFIX + "tab2.html"
MASS_ATTENUATION_COEFFS_URL = MASS_ATTENUATION_COEFFS_PREFIX + "tab4.html"
ZMAX = 92


def densities_table(html):
    tab = html.body.find('table')
    names = []
    data = []
    for tr in tab.find_all('tr')[3:]:
        tds = tr.find_all('td')
        if not tds:
            continue
        names.append(tds[0].text)
        i = 3
        if tr.find_all('td', attrs={'rowspan':"50"}):
            i = 6
        data.append(float(tds[i].text))
    return names, data


def links_table(html):
    names = []
    urls = []
    tab = html.body.find('table')
    for a in tab.find_all('a'):
        names.append(a.text)
        urls.append(MASS_ATTENUATION_COEFFS_PREFIX + a.get("href"))
    return names, urls


def mass_coeff_table(html):
    main_tab = html.body.find('table')
    tab = main_tab.find('table')
    trs = tab.find_all('tr')
    name = trs[0].find('b').text
    name = name[:name.find('\n')]
    data = []
    for tr in trs[5:]:
        if not tr.find_all('td'):
            continue
        row = []
        for td in tr.find_all('td'):
            for field in td.text.strip().split(' '):
                try:
                    row.append(float(field))
                except ValueError:
                    continue
        data.append(row)
    return name, data


def find_best(name, names):
    best = -1
    best_score = 0
    for i, candidate in enumerate(names):
        common = os.path.commonprefix([name.lower(), candidate.lower()])
        score = len(common)
        if score == len(name):
            return i
        elif score > best_score:
            best_score = score
            best = i
    return best


if __name__ == "__main__":
    resp = requests.get(DENSITIES_URL)
    if not resp.ok:
        print("Cannot fetch {}".format(DENSITIES_URL))
        raise IOError
    names, densities = densities_table(bs(resp.text))

    elements = []
    resp = requests.get(MASS_ATTENUATION_COEFFS_URL)
    if not resp.ok:
        print("Cannot fetch {}".format(MASS_ATTENUATION_COEFFS_URL))
        raise IOError
    names_unsorted, urls = links_table(bs(resp.text))
    for i, (name, dens) in enumerate(zip(names, densities)):
        print(name)
        url = urls[find_best(name, names_unsorted)]
        resp = requests.get(url)
        if not resp.ok:
            print("Cannot fetch {}".format(url))
            break
        _, data = mass_coeff_table(bs(resp.text))

        elements.append([name, dens])
        # Save the attenutions table
        with open('c{:02d}.csv'.format(i + 1), 'w') as f:
            f.write('"energy [MeV]", "mu [cm2/g]", "mu_en [cm2/g]"\n')
            for elem in data:
                f.write('{},{},{}\n'.format(elem[0], elem[1], elem[2]))

    # Save the elements table
    with open('compounds.csv', 'w') as f:
        f.write('"Name", "dens [g/cm3]"\n')
        for elem in elements:
            f.write('"{}",{}\n'.format(elem[0], elem[1]))
