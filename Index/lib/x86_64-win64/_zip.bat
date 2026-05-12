del po-ors.zip
cd Search
del *.* /q
cd ..

copy Index_pr.exe PO.exe

powershell Compress-Archive -Force -Path Data, Search, Programdata, PO.exe -DestinationPath po-ors.zip

copy PO.zip D:\Google_disk\tmp\po-ors.zip

del PO.exe