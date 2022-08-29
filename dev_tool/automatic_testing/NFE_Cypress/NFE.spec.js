// NFE.spec.js created with Cypress
//
// Start writing your Cypress tests below!
// If you're unfamiliar with how Cypress works,
// check out the link below and learn how to write your first test:
// https://on.cypress.io/writing-first-test


// describe('NeuroFeature Extractor Automatic Test', () => {

const TEST_NUM = 40;

const WIDTH = 1000, HEIGHT = 1200; // for in browser test only


Cypress._.times(TEST_NUM, () => {

    it('NFE automatic test.', () => {
        cy.viewport(WIDTH, HEIGHT)

        cy.visit('https://hbp-bsp-hhnb.cineca.it:17895/efelg/')

        cy.contains('Next').click()

        cy.url().should('include', 'show_traces')

        /*
        var contributors_length = cy.get('table#contributors > div > label').

        cy.get('table#contributors > div > label').each((contributor, idx) => {
            cy.debug(contributor, idx);
        }) 
        */

        cy.contains('cac').click({force: true})
        cy.contains('Apply').click({force: true})
        cy.get('#wait-message-div').should('be.visible')
        cy.get('#wait-message-div').should('be.not.visible')
        
        cy.get('.cell_selall').each(($cell) => {
                cy.wrap($cell).click({force: true})
        })

        cy.get('#next_checkbox').click({force: true})
        cy.contains('Next').click()

        cy.get('.overlay-content').should('be.visible')
        cy.get('#e-st-user-choice-accept-btn').click({force: true})

        cy.url().should('include', 'select_features')
        cy.contains('Spike event features').click()
        cy.contains('Spike shape features').click()
        cy.contains('Voltage features').click()
        cy.wait(1000)
        cy.get('.span-check').each(($feature) => {
            var r = Math.random()
            if (r > 0.5) {
                cy.wrap($feature).click({force: true})
            }
        })
        cy.contains('Next').click()

        cy.wait(5000)
        cy.get('.spinner-border', {timeout: 600000}).should('be.not.visible')
        cy.get('#wmd-first').contains('Error').should('not.exist')
    })
  })
  

