# signInUCSD
Simple sign-in system using UCSD ID cards. Allows users to sign-up by filling out a simple one time form. Allows administrators to set user permissions and track sign-ins.

## Deploying on Ubuntu 16.04 EC2 on AWS
Instructions on how to use Nginx to deploy multiple static websites and how to use it as a reverse proxy for a Flask application. I am simply reiterating all the information I have learned from the resources available below, but I will be only including the steps that I used and needed.

### Nginx
Installing Nginx by using the package manager.
```
sudo apt-get install nginx
```

I will list some commands that you can use to control Nginx once you have it installed.  

This will restart Nginx which is useful when you are changing the configuraiton files.
```
sudo service nginx restart
```

This will stop nginx.
```
sudo service nginx stop
```

This will start nginx.
```
sudo service nginx start
```


### Serving static websites
1. Remove the default server block configuration.
```
sudo rm /etc/nginx/sites-enabled/default
```
Note: All the actual configuration files will be stored in ```/etc/nginx/sites-available/```. When you actually want to use them, you symbolically link the files in ```sites-availble``` to ```/etc/nginx/sites-enabled```. In step 1, we don't actually delete the ```default``` file, but we delete the symbolic link to it. It still exists in ```sites-availble```.

2. Create a new configuration file.
```
sudo vim /etc/nginx/sites-enabled/static
```
In this example, we call the file ```static```, but you can call it anything you want.

3. In the file, create a server block by entering in the following.
```
server {
    listen 80;

    server_name *.mothakes.com mothakes.com;

    root /var/www/html;

    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}
```
I will briefly explain the purpose of each line.
* ```server { }``` specifies a server block detailing certain setttings.
* ```listen 80;``` specifies which port this block will be listening on. Port 80 is the default port that web browsers use to access websites. This is the ```http``` portion of the url. This is different than if it is ```https``` which is port 443.
* ```server_name *.mothakes.com mothakes.com;``` specifies which domain names this block applies to. This specific block applies to ```www.mothakes.com```, ```anything.mothakes.com```, and ```mothakes.com```. The ```*``` is a wildcard allowing the subdomain to be anything.
* ```root /var/www/html;``` specifies where this server block will look for files for this website. Here it looks for files in ```/var/www/html```
* ```index index.html;``` spcifies what will the index files will be ie. which files will be served if the plain domain name is requested.
* ```location / { }``` specifies what happens when this url is requested. I am not sure what ```try_files``` does, but it is required I believe.

4. After saving the file, you need to symbolically link it in ```sites-enabled``` for it to work.
```
cd /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/static .
```

5. Restart Nginx. If all your syntax is correct, there should be no output from this command.
```
sudo service nginx restart
```

6. Create an index file in ```/var/www/html```, so that it can be served.
```
sudo vim /var/www/html/index.html
```
Enter the following into the file. This is just a basic HTML file, you may change this to anything you want, but for now we'll use this to make sure our site works.
```
<!DOCTYPE html>

<html>

<head>
</head>

<body>
This is my static website.
</body>

</html>
```

7. Visit your domain name and you should see your website. In my case, go to [www.mothakes.com](https://www.mothakes.com)

### Using Nginx as Reverse Proxy for Flask Applications
I will be going through how you can use Nginx as reverse proxy for a Flask application. What this essentially means is that Nginx will forward requests to a Flask application running locally and return the responses from Flask to the clients.

1. Start your flask application. In this case, my signInUCSD application which I run by issuing the following command in the same directory as the file.
```
python signInUCSD.py
```
This will start the program and it will listen on port 5000. You can test this by allowing Inbound Traffic on port 5000 and going to IP address of your server on port 5000. You should see your website files appearing.

2. Remove the default server block configuration.
```
sudo rm /etc/nginx/sites-enabled/default
```
Note: All the actual configuration files will be stored in ```/etc/nginx/sites-available/```. When you actually want to use them, you symbolically link the files in ```sites-availble``` to ```/etc/nginx/sites-enabled```. In step 1, we don't actually delete the ```default``` file, but we delete the symbolic link to it. It still exists in ```sites-availble```.

3. Create a new configuration file.
```
sudo vim /etc/nginx/sites-enabled/flask
```
In this example, we call the file ```flask```, but you can call it anything you want.

4. In the file, create a server block by entering in the following.
```
server {
    listen 80;
    listen [::]:80;

    server_name ieee.mothakes.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
```
I will briefly explain the purpose of each line.
* ```server { }``` specifies a server block detailing certain setttings.
* ```listen 80;``` specifies which port this block will be listening on. Port 80 is the default port that web browsers use to access websites. This is the ```http``` portion of the url. This is different than if it is ```https``` which is port 443.
* ```server_name ieee.mothakes.com;``` specifies which domain names this block applies to. This specific block applies to ```ieee.mothakes.com```. You may note that this overlaps with ```*.mothakes.com```. However, Nginx matches the url as closely as possible so ```ieee.mothakes.com``` will use this server block over the the one with ```*.mothakes.com```.
* ```location / { }``` specifies what happens when this url is requested. In this case, it redirects all requests to ```http://127.0.0.1:5000```.
* ```proxy_pass http://127.0.0.1:5000;``` specifies where to reverse proxy the requests to. This is the port and address that the Flask application is listening on.
* ```proxy_set_header Host $host;``` the name and port of the NGINX server.
* ```proxy_set_header X-Real-IP $remote_addr;``` the IP address of the user.

5. After saving the file, you need to symbolically link it in ```sites-enabled``` for it to work.
```
cd /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/flask .
```

6. Restart Nginx. If all your syntax is correct, there should be no output from this command.
```
sudo service nginx restart
```
7. Visit your domain name and you should see your website. In my case, go to [ieee.mothakes.com](https://ieee.mothakes.com)

### Obtaining an SSL Certificate
I will show all the steps required to setup your website with SSL encryption. What this basically means is that all data sent will not be sent "in the clear". This is useful when you're receiving sensitive data such as passwords and do not want anybody to be able to see it. Additonally, it will give your site the little green lock in the browser and allow ```https``` connections.
1. Installing Certbot
Add the repo.
```
sudo add-apt-repository ppa:certbot/certbot
```
Press ```Enter``` to accept the addition.
```
sudo apt-get update
```
Install Certbot using ```apt-get```.
```
sudo apt-get install python-certbot-nginx
```

2. Obtaining the certificates.
You can add as many subdomains as you want, but wildcard domains such as ```*.mothakes.com``` will not work. You need to specify all the separate subdomains using the ```-d``` flag as we I have done below. 
```
sudo certbot --nginx -d www.mothakes.com -d mothakes.com -d ieee.mothakes.com
```
You will be prompted to choose whether or not to redirect all ```HTTP``` traffic to ```HTTPS``` with the following prompt.
```
Please choose whether or not to redirect HTTP traffic to HTTPS, removing HTTP access.
-------------------------------------------------------------------------------
1: No redirect - Make no further changes to the webserver configuration.
2: Redirect - Make all requests redirect to secure HTTPS access. Choose this for
new sites, or if you're confident your site works on HTTPS. You can undo this
change by editing your web server's configuration.
-------------------------------------------------------------------------------
Select the appropriate number [1-2] then [enter] (press 'c' to cancel):
```

I choose option 2 which means you can only access those domains using ```HTTPS```. All ```HTTP``` traffic will be automatically redirected to ```HTTPS```.  

If it's succesful you should get a similar message.
```
Congratulations! You have successfully enabled https://www.mothakes.com,
https://mothakes.com, and https://ieee.mothakes.com

You should test your configuration at:
https://www.ssllabs.com/ssltest/analyze.html?d=www.mothakes.com
https://www.ssllabs.com/ssltest/analyze.html?d=mothakes.com
https://www.ssllabs.com/ssltest/analyze.html?d=ieee.mothakes.com
-------------------------------------------------------------------------------

IMPORTANT NOTES:
 - Congratulations! Your certificate and chain have been saved at:
   /etc/letsencrypt/live/www.mothakes.com/fullchain.pem
   Your key file has been saved at:
   /etc/letsencrypt/live/www.mothakes.com/privkey.pem
   Your cert will expire on 2018-02-23. To obtain a new or tweaked
   version of this certificate in the future, simply run certbot again
   with the "certonly" option. To non-interactively renew *all* of
   your certificates, run "certbot renew"
 - Your account credentials have been saved in your Certbot
   configuration directory at /etc/letsencrypt. You should make a
   secure backup of this folder now. This configuration directory will
   also contain certificates and private keys obtained by Certbot so
   making regular backups of this folder is ideal.
 - If you like Certbot, please consider supporting our work by:

   Donating to ISRG / Let's Encrypt:   https://letsencrypt.org/donate
   Donating to EFF:                    https://eff.org/donate-le

```
3.  Testing your new certifcates by visiting their corresponding URL's and looking for the little green lock indicating a secure connection.

4. Verifying Certbot Auto-Renewal
```
sudo certbot renew --dry-run
```
This should run with no errors.

### Solutions to Common Problems
If you have trouble accessing the website and you think everything went fine make sure the following is true:
* Domain is pointing correctly at your server's IP address.
* EC2 Security Group Settings allow for Inbound Traffic for HTTP and HTTPS.


### Resources
[Proxying using Nginx, Gunicorn](https://www.youtube.com/watch?v=kDRRtPO0YPA)  
[Reasons Proxying](https://serverfault.com/questions/331256/why-do-i-need-nginx-and-something-like-gunicorn)  
[How to Nginx](http://www.patricksoftwareblog.com/how-to-configure-nginx-for-a-flask-web-application/)  
[Removing all PIP packages](https://stackoverflow.com/questions/11248073/what-is-the-easiest-way-to-remove-all-packages-installed-by-pip)   
[SSL Certificates](https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-16-04)  
