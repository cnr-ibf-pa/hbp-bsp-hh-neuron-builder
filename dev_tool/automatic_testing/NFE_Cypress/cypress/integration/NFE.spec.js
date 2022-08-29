// NFE.spec.js created with Cypress
//
// Start writing your Cypress tests below!
// If you're unfamiliar with how Cypress works,
// check out the link below and learn how to write your first test:
// https://on.cypress.io/writing-first-test


describe('NeuroFeatures Extractor', () => { 

    it('NFE automatic test.', () => {
        cy.visit('https://hbp-bsp-hhnb.cineca.it/efelg/')

        cy.contains('Next').click()

        cy.url().should('include', 'show_traces')

        cy.contains('cac', {timeout: 60000}).click({force: true})
        cy.contains('Apply').click({force: true})
        
        cy.get('#wait-message-div', {timeout: 60000}).should('be.visible')
        cy.get('#wait-message-div', {timeout: 600000}).should('be.not.visible')

        cy.get('.cell_selall', {timeout: 60000}).each(($cell) => {
                cy.wrap($cell).click({force: true})
        })

        cy.get('#next_checkbox').click({force: true})
        cy.contains('Next').click()

        cy.get('.overlay-content').should('be.visible')
        cy.get('#e-st-user-choice-accept-btn').click({force: true})

        cy.url().should('include', 'select_features')

        cy.get('.span-check', {timeout: 60000}).each(($feature) => {
            var r = Math.random()
            if (r > 0.5) {
                cy.wrap($feature).click({force: true})
            }
        })
        cy.contains('Next').click()

        cy.get('.spinner-border', {timeout: 60000}).should('be.visible')
        cy.get('.spinner-border', {timeout: 600000}).should('be.not.visible')
        cy.get('#wmd-first').contains('Error').should('not.exist')
    })
})

