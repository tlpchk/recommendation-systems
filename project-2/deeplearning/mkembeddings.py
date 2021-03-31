#!/usr/bin/env python3

from pymagnitude import Magnitude, MagnitudeUtils
import numpy as np
from tqdm import tqdm

import sys
import re
import json

DEFAULT_MODEL = "word2vec/light/GoogleNews-vectors-negative300"


if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} <json-path> <output-path>")
    exit(1)

json_fp = sys.argv[1]
output_fp = sys.argv[2]

texts_dict = None
with open(json_fp, 'r') as f:
    texts_dict = json.load(f)

print("Downloading model", DEFAULT_MODEL)
magnitude_fp = MagnitudeUtils.download_model(DEFAULT_MODEL)
print("Done!")
magnitude = Magnitude(magnitude_fp)

output_dict = {}
for key, value in tqdm(texts_dict.items()):
    if value is None:
        continue 
    words = value.split()
    words = [re.sub("[^A-Za-z0-9\-]", "", w) for w in words]
    embeddings = magnitude.query(words)
    sentence_embeddings = np.mean(embeddings, axis=0)
    output_dict[key] = sentence_embeddings
np.savez(output_fp, **output_dict)

