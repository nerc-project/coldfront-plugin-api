set -xe

PATCH_FILE="$(pwd)/patches/01_add_api_urls.patch"
echo "$PATCH_FILE"

TARGET_CD=$(python -c "import pkgutil; print(pkgutil.get_loader('coldfront.config.urls').path.split('coldfront/config/urls.py')[0])")
cd "$TARGET_CD" && patch -p1 < "$PATCH_FILE"
