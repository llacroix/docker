docker login
version=(8 9 10 11 12)
repo="llacroix/odoo"

for version in "${version[@]}"
do
    cd "${version}.0"
    docker build -t odoo:${version} .
    docker tag odoo:${version} $repo:${version}
    docker push $repo:${version}
    cd ..
done
