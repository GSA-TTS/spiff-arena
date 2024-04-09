### Final catch up for deployments
When determining what the gap was in relation to Bret v Alex pushing the manifest and deploying the running application with successful login via the frontend, it was determined that we need to add the `public_networks_egress` to the sandbox in which we are attempting to deploy.
```
cf bind-security-group public_networks_egress ORGNAME --lifecycle running --space SPACENAME
```

### Deploying
- Create a database service
- Copy vars.yml-template to `vars.yml`
- `cf push --vars-file vars.yml`

