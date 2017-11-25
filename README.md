# signInUCSD
Simple sign-in system using UCSD ID cards. Allows users to sign-up by filling out a simple one time form. Allows administrators to set user permissions and track sign-ins.

## Deploying on Ubuntu 16.04 EC2 on AWS
Instructions on how to use Nginx to deploy multiple static websites and how to use it as a reverse proxy for a Flask application. I am simply reiterating all the information I have learned from the resources available below, but I will be only including the steps that I used and needed.

### Ngninx
Installing Nginx by using the package manager.
```
sudo apt-get install nginx
```

I will list some commands that you can use to control Ngninx once you have it installed.  

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


### Resources
[Proxying using Nginx, Gunicorn](https://www.youtube.com/watch?v=kDRRtPO0YPA)  
[Reasons Proxying](https://serverfault.com/questions/331256/why-do-i-need-nginx-and-something-like-gunicorn)  
[How to Nginx](http://www.patricksoftwareblog.com/how-to-configure-nginx-for-a-flask-web-application/)  
[Removing all PIP packages](https://stackoverflow.com/questions/11248073/what-is-the-easiest-way-to-remove-all-packages-installed-by-pip)   
[SSL Certificates](https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-16-04)  
