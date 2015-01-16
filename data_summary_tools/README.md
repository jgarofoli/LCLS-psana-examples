# Data Summary Tool

A tool to prepare an html report of the data run.
Uses bootstrap and a couple of other packages, but the dependencies 
are packaged in this directory.

## Checkout just this directory

Use git sparse checkout.

```
git init data_summary
cd data_summary
git remote add -f origin https://github.com/jgarofoli/LCLS-psana-examples.git
git config core.sparsecheckout true
echo "data_summary/" >> .git/info/sparse-checkout
git pull origin master
```

From http://stackoverflow.com/a/13738951
