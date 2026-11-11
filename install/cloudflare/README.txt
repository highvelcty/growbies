#!/bin/bash

# Growbies Cloudflare Database Proxy Setup

## Overview

Execute `./install.sh <HOSTNAME>` to install `growbies-db-proxy` systemd service as well as a
credential file.

Growbies can connect to a remote PostgreSQL database through a Cloudflare Access TCP proxy.

The client machine runs `cloudflared` as an independent systemd service. This establishes a local
TCP endpoint that forwards connections through Cloudflare Access to the remote database.

The Growbies application is independent of this service. It simply connects to the configured
database address and port.

Database endpoint:

    127.0.0.1:15432

The Cloudflare proxy is optional and is not required for installations using a local database or
 another networking solution.

## 1. Cloudflare Tunnel Configuration

The remote database server must already be accessible through a Cloudflare Tunnel.

The Cloudflare Tunnel must have a published application route associating this hostname with the
PostgreSQL service on the remote database host.

The route must point to the appropriate PostgreSQL TCP endpoint.

The client-side `cloudflared access tcp` command connects to this hostname.

Note that TCP applications require `cloudflared` on the client machine as well as the machine
hosting the remote service.

Cloudflare documentation:
https://developers.cloudflare.com/cloudflare-one/access-controls/applications/non-http/cloudflared-authentication/

## 2. Cloudflare Access Application and Policy

The database hostname must be protected by a Cloudflare Access application.

In the Cloudflare Zero Trust dashboard:

1. Navigate to Access > Applications.
2. Create or select the self-hosted application protecting `db-norlong.growbies.net`.
3. Configure the application hostname to match the database hostname.
4. Create an Access policy to authorize the client service token.

The policy should have:

    Action: Service Auth

    Include:
        Selector: Service Token
        Value: growbies-norlong-db-client

The Service Auth policy allows clients presenting the associated service token credentials to
access the protected application without interactive browser authentication.

Do not rely on an ordinary browser-based Allow policy for headless service authentication.

## 3. Create a Cloudflare Access Service Token

In the Cloudflare Zero Trust dashboard:

1. Navigate to Access controls > Service credentials > Service Tokens.
2. Select Create Service Token.
3. Use the following name:

       growbies-norlong-db-client

4. Select an appropriate expiration duration.
5. Create the token.

Cloudflare provides two credentials:

- Client ID
- Client Secret

Save both values securely. The Client Secret is only displayed when initially generated
(or subsequently rotated).

These credentials are used by the client-side `cloudflared access tcp` process to access the
growbies db.

Service token documentation:
https://developers.cloudflare.com/cloudflare-one/access-controls/service-credentials/service-tokens/
