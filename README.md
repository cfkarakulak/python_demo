# Instructions for using this App for Demo purposes

[![CircleCI](https://circleci.com/gh/verygoodsecurity/python_demo.svg?style=svg)](https://circleci.com/gh/verygoodsecurity/python_demo)

This demo app demonstrates the typical scenario for operating with sensitive data to showcase how a customers apps can be integrated with VGS to secure data.

## Use case

In this application there are 2 customer services (Order Service and Merchant Portal) and a 3rd party payment processing service.

This represents a typical payments processing scenario where a customer submits a payment card to a merchant to pay for a service and then the merchant submits the card data to a payment processor to charge the card.

Users can go to Order Service and place order(s) with their payment's data (card number, billing address, etc). When user places an order the payment information is stored in customer's storage. It can be later processed in Merchant Portal.
An authorized user of Merchant Portal can charge the payment - this action initiates call to an external Payment Service.

- Order Service (http://localhost:8080)
- Merchant Portal (http://localhost:8080/merchant_admin/payments)
- Payment Service (http://localhost:8080/processor_admin/charges)

## Demo scenario

In this exercise we will cover the following two scenarios

#### Capture data without VGS

See how data flows through these services without VGS:

- go to Order Service, fill in the payment data and place an order (you can use auto-generated values or find fake credit cards numbers here: http://www.getcreditcardnumbers.com/)
- go to Merchant Portal and verify the corresponding payment was created
- charge the payment on Merchant Portal
- go to the Payment Service and verify the payments data was received

You will see that payment card data is stored in the merchant's system bringing them in to PCI scope.

#### Secure these services with VGS

Configure VGS Proxy to redact sensitive data sent to the Order Service and reveal data when sending payment's information to Payment System:
- go to https://dashboard.verygoodsecurity.com and configure VGS Proxy to redact the sensitive data on the way in (credit card number and CVV code)
- go to Order Service, fill payment data and place an order
- go to Merchant Portal and verify the payment's info does NOT contain a sensitive information
- go to https://dashboard.verygoodsecurity.com and configure VGS Proxy to reveal the sensitive data on the way out (when sent to Payment Service)
- go to the Payment Service and verify the payments data with the actual credit card number/CVV code was received

## Run Demo App
We are going to use [Docker](https://docker.com) to run the app.

### Build

```bash
docker build . -t python_demo
```

### Run

```bash
docker run -it \
   -p 3000:3000 -p 3001:3001 -p 8080:8080 \
   --rm --name python_demo -v $(pwd):/opt/app/src \
   python_demo
```

### Alternatively deploy minikube and Helm and use a "helm chart" to deploy
[minikube](https://github.com/kubernetes/minikube)    
[helm](https://github.com/helm/helm/blob/master/docs/install.md)

```bash
cd python_demo/kubernetes/helm/python_demo_chart
helm install --namespace=pythondemo --name python-demo-1.0.0 .
```

### Expose to Internet

In order to integrate the app running on your local machine with VGS proxy you'll have to expose the app to the internet.

Use ngrok. This handy tool lets you set up a secure tunnel to your localhost, which is a fancy way of saying it opens access to your local app from the internet.

#### Step 1: Install ngrok
Go to https://ngrok.com/download and download the version that corresponds to your platform.

**Ngrok with TLS**

If you're running over TLS make sure to set the host header to help flask know how to redirect to the host correctly.

**If you have paid version of ngrok** you can use a command like this to have fixed subdomain:
```
ngrok http  -subdomain=vgssl6 -host-header=tntq2xam5lo.sandbox.verygoodproxy.com 8080
```
**If you have free version of ngrok** you can use a command like this, and your domain will be different on each ngrok run:
```
ngrok http -host-header=tntq2xam5lo.sandbox.verygoodproxy.com 8080
```

#### Step 2: Route requests to Payment Service to go via ngrok

To be able to configure VGS proxy for requests going to Payment Service(`/charge` endpoint) your app should route these requests via ngrok, `VGS_PROCESSOR_ROOT_URL` environment variable should be set:

```bash
docker run -it \
   -p 3000:3000 -p 3001:3001 -p 8080:8080 \
   --rm --name python_demo -v $(pwd):/opt/app/src \
   -e HTTPS_PROXY=https://user:pass@proxy.com:port \
   -e VGS_PROCESSOR_ROOT_URL=https://e907262d.ngrok.io/charge \
   python_demo
```
* NOTE: `user:pass` is an access credentials which you can find [on your dashboard](https://www.verygoodsecurity.com/docs/settings/access-credentials)

## Set up VGS
Some quick tips on how to set up VGS connections for use with this application.

### Inbound Connection
(Reference: https://www.verygoodsecurity.com/docs/guides/inbound-connection).

* Use reverse proxy URL to access Order Service, e.g. `https://tntywefqyrb.SANDBOX.verygoodproxy.com`
* Set upstream to ngrok address, e.g. `https://e907262d.ngrok.io`
* Filter condition should be PathInfo equals `/payment`
* Operation is to **REDACT** form fields:
    - `card-number`
    - `card-security-code`

### Outbound Connection
(Reference: https://www.verygoodsecurity.com/docs/guides/outbound-connection).

* Set `HTTPS_PROXY` to forward proxy URL
* Set `VGS_PROCESSOR_ROOT_URL` to something like this: `https://e907262d.ngrok.io/charge`
* Set upstream to ngrok address, just like with the inbound connection
* Filter condition should be PathInfo equals `/charge`
* Operation is to **REVEAL** JSON fields:
    - `$.card`
    - `$.card_security_code`

## Integration with VGS Satellite

* Run this demo using ngrok, commands listed [here](#expose-to-internet)
* Clone [VGS Satellite](https://github.com/verygoodsecurity/vgs-satellite)
* Run VGS Satellite using default environment variables specified in .env
```bash
docker-compose up
```
* Run request:
```bash
curl -x http://localhost:1230 http://e907262d.ngrok.io/payment -d "name=Bob+Jones&billing_address=1+Dr+Carlton+B+Goodlett+Pl%2C+San+Francisco%2C+CA+94102&card-number=5105105105105100&card-expiration-date=12%2F20&card-security-code=123&url=verygoodsecurity.com"
```
* Open [http://localhost:1234](http://localhost:1234)
* Wait for your requests to appear
* Choose your request from the list
* Click secure you payload
* Check field you would like to secure
* Click `Secure this payload`, then `View route configuration`
* Download inbound/outbound route and reference instructions provided to import your first route on VGS Dashboard
## Used Technologies/Tools:

HTML, CSS, JS, scss, Gulp, NPM, Git, Python
