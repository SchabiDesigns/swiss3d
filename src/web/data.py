import numpy as np
import pandas as pd
import pickle
import zipfile
import requests
import io
import os


LINKS = {
    "dhm25" : r"https://cms.geo.admin.ch/ogd/topography/DHM25_MM_ASCII_GRID.zip",
    "dhm200": r"https://data.geo.admin.ch/ch.swisstopo.digitales-hoehenmodell_25/data.zip"
}

CACHE_PATH = "data/cache/"

def read_file_lines(filepath, **kwargs):
    file = open(filepath, 'r')
    return file.readlines()

def parse_lines(lines, n_head_lines, **kwargs):

    header = lines[:n_head_lines]
    data = [line.strip().split(" ") for line in lines[n_head_lines:]]
    flat = []
    for line in data:
        flat += line
    flat = list(map(float, flat))

    meta = {head.split(" ")[0].lower():float(head.split(" ")[-1].strip()) for head in header}
    for key, value in meta.items():
        if int(value)==value:
            meta[key] = int(value)

    if len(flat)/meta["nrows"]==meta["ncols"]:
        return flat, meta
    else:
        print("failed:", len(flat)/meta["nrows"],"not",meta["ncols"])
        return None, None

def create_dataframe(data, meta, **kwargs):
    
    chunks = [data[x:x+meta["ncols"]] for x in range(0, len(data), meta["ncols"])]

    x = np.ones(meta["ncols"]).cumsum()
    x -= 1 
    x *= meta["cellsize"]
    x += meta["xllcorner"]
    y = np.ones(meta["nrows"]).cumsum()
    y -= 1
    y *= meta["cellsize"]
    y += meta["yllcorner"]
    y = np.flip(y)

    swiss = pd.DataFrame(chunks, columns=x, index=y)
    swiss.replace(meta["nodata_value"], np.nan, inplace=True)
    print("shape:",swiss.shape)
    return swiss

def download_file(url):

    path = CACHE_PATH

    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    asc_files = [file for file in z.namelist() if file.endswith(".asc")]
    if len(asc_files)==1:
        z.extract(asc_files[0], path=path)
        return path + asc_files[0]
    else:
        print("no or multiple asc files found!")
        return None

def structure_file(filepath):

    lines = read_file_lines(filepath)
    
    data, meta = parse_lines(lines, n_head_lines=6)

    if not data==None:
        df = create_dataframe(data, meta)
        return df, meta
    else:
        return None, None

def check_cache(file):
    print(file)
    if file in ["dhm25", "dhm200"]:
        try:
            with open(CACHE_PATH + file + ".pkl",'rb') as f:
                df, meta = pickle.load(f)
            return df, meta
        except:
            print("file not in cache... try to download")
            #try:
            filepath = download_file(LINKS.get(file))
            print("file downloaded")
            
            df, meta = structure_file(filepath)
            print("file structured")
            with open(CACHE_PATH + file + ".pkl", 'wb') as f:  # open a text file
                pickle.dump((df, meta), f) # serialize the list
            os.remove(filepath)
            return df, meta
            # except Exception as e:
            #     print("download failed", e)
            #     return None, None
    else:
        print("not known file")
        return None, None