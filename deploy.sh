docker login
version=(8 9 10 11 12 13)
repo="llacroix/odoo"

for version in "${version[@]}"
do
    cd "${version}.0"
    docker build -t local-odoo:${version} .
    docker tag local-odoo:${version} $repo:${version}
    docker push $repo:${version}
    cd ..
done
