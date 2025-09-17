set -xe

# If running on Github actions, don't create a virtualenv
if [[ ! "${CI}" == "true" ]]; then
    virtualenv -p python3 /tmp/coldfront_venv
    source /tmp/coldfront_venv/bin/activate
fi

python -m pip install --upgrade pip
pip3 install -e .
pip3 install -r test-requirements.txt

./ci/patch_coldfront_urls.sh
