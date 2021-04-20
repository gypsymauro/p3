Library for P3

clone the library with git commands, 
then copy the template ini file in a p3restapi.ini filename and edit with the correspondent parameters,
place the certificates in the parent directory and call the script from the parent directory
so it will works as module as well

hints to extract pem certificates and key without pwd from pfx file:

Step 1
Extract the private key from the .pfx file (you need to know the password:

openssl pkcs12 -in [certificate.pfx] -nocerts -out [certificate-key-encrypted.key]

Step 2
Now lets decrypt the key:

openssl rsa -in [certificate-key-encrypted.key] -out [certificate-key-decrypted.key]

openssl rsa -in [certificate-key-encrypted.key] -out [certificate-key-decrypted.key]

Step 3
Now lets extract the public certificate:

openssl pkcs12 -in [certificate.pfx] -clcerts -nokeys -out [certificate.crt]

Step 4
You also need all the public certs in the chain up to the root. I’m talking about these:
Root and Intermediate Certs

Step 5
now create a new text file (don’t use notepad) and put your public, private, intermediate public and root public together. It’s simple and should look like this:

-----BEGIN CERTIFICATE-----
### Replace with your public certificate ###
### From step 3 above ###
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
### replace with your intermediate public cert ###
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
### replace with your root public cert ###
-----END CERTIFICATE-----
-----BEGIN RSA PRIVATE KEY-----
### replace me with your .key file ###
### from step 2 above ###
-----END RSA PRIVATE KEY-----

Save the file as a .pem file.
If you want to view the cert on windows, simply rename the .pem to .cer

Thanks to:
https://www.edrockwell.com/blog/certificates-convert-pfx-to-pem-and-remove-the-encryption-password-on-private-key/



