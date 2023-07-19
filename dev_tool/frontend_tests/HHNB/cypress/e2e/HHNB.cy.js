// HHNB.spec.js created with Cypress
//
// Start writing your Cypress tests below!
// If you're unfamiliar with how Cypress works,
// check out the link below and learn how to write your first test:
// https://on.cypress.io/writing-first-test

Cypress.Cookies.debug(true);

Cypress.on('uncaught:exception', (err, runnable) => {
    return false;
});

  
describe("Hodgkin-Huxley Neuron Builder Automatic Tests", () => {

    before(() => {
        // login using saved cookie session from real context
        const sessionId = Cypress.env('sessionid')
        cy.setCookie('sessionid', sessionId)     

        cy.fixture('features.json', {encoding: null}).as('featuresFile')
        cy.fixture('protocols.json', {encoding: null}).as('protocolsFile')
        cy.fixture('W_20220524124955_orig_model.zip', {encoding: null}).as('modelZip')
    })

    beforeEach(() => {
        // prevents cookie clearing before each test
        Cypress.Cookies.defaults({
            preserve: 'sessionid'
        })
    })

    /*it ("Create workflow", () => {
        cy.visit('https://127.0.0.1:8000/hh-neuron-builder/')        
        cy.get('#new-wf').click()
        cy.url({timeout: 6000}).should('include', 'workflow')
        cy.get('.loading-animation.sublayer', {timeout: 60000}).should('be.not.visible')
    
    })
*//*
    it ("Run Optimization", () => {

        cy.visit('https://hbp-bsp-hhnb.cineca.it:17895/hh-neuron-builder/')        
        cy.get('.logout').should('exist')

        cy.get('#new-wf').click()

        cy.wait(2000)
        cy.url({timeout: 6000}).should('include', 'workflow')
        cy.get('.loading-animation.sublayer', {timeout: 60000}).should('be.not.visible')
    
        // upload features
        cy.get('#feat-up-btn').click()
        cy.get('#formFile').selectFile(['@featuresFile', '@protocolsFile'])
        cy.get('#uploadFormButton').click()

        cy.get('#opt-up-btn').click()
        cy.get('#formFile').selectFile('@modelZip')
        cy.get('#uploadFormButton').click()

        cy.get('#opt-set-btn').click({force: true})
        cy.wait(1000)
        cy.get('#accordionSADaint').click()
        cy.wait(1000)
        cy.get('#sa-daint-node-num').clear().type(2)
        cy.wait(1000)
        cy.get('#apply-param').click({force: true})
        cy.wait(1000)
        cy.get('#launch-opt-btn').click({force: true})

        cy.contains('Job submitted', {timeout: 6000}).should('be.visible')
    }) */ 

    it ("Run Simulation", () => {
        cy.visit('https://hbp-bsp-hhnb.cineca.it/hh-neuron-builder/')        
        cy.get('.logout').should('exist')
        cy.wait(Math.random() + 1)
        cy.get('#new-wf').click({force: true})
        // cy.wait(6000)
        cy.url({timeout: 60000}).should('include', 'workflow')
        cy.get('.loading-animation.sublayer', {timeout: 6000}).should('be.not.visible')
    
        cy.get('#opt-fetch-btn', {timeout: 6000}).click({force: true})
        cy.get('button#jobsSADaint').click({formce: true})
        cy.wait(2000)
        cy.get('.spinner-border', {timeout: 6000}).should('be.not.visible')
        cy.get('#7845AB74-3B9F-4283-ABB5-A4858085903B').click({force: true})
        cy.wait(2000)
        cy.get('#progressBarFetchJob', {timeout: 60000}).should('be.not.visible')
        cy.wait(2000)
        cy.contains('Run Simulation').click({force: true})
        cy.contains('Error').should('not.exist') 
    })
})
