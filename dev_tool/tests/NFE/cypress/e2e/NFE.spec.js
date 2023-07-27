// NFE.spec.js created with Cypress
//
// Start writing your Cypress tests below!
// If you're unfamiliar with how Cypress works,
// check out the link below and learn how to write your first test:
// https://on.cypress.io/writing-first-test


describe('NeuroFeatureExtract automatic tests.', () => {

  const URL = Cypress.env('host').concat('/efelg/');

  it('NFE whole workflow test.', () => {
    cy.visit(URL);

    cy.contains('Next').click();

    cy.url().should('include', 'show_traces');

    cy.contains('cac', {timeout: 60000}).click({force: true});
    cy.contains('Apply').click({force: true});

    cy.get('.cell_selall', {timeout: 600000}).each(($cell) => {
        cy.wrap($cell).click({force: true});
    }),

    cy.get('#next_checkbox').click({force: true});
    cy.contains('Next').should('be.enabled').click();

    cy.get('.overlay-content').should('be.visible');
    cy.get('#e-st-user-choice-accept-btn').click({force: true});

    cy.url().should('include', 'select_features');

    cy.get('.span-check', {timeout: 60000}).each(($feature) => {
        var r = Math.random();
        if (r > 0.5) {
            cy.wrap($feature).click({force: true});
        }
    });
    cy.contains('Next').click();

    cy.get('#wmd-first').contains('Error').should('not.exist');
    cy.get('.btn.btn-lg.btn-success', { timeout: 60000 }).should('be.enabled');
  });

  it('NFE upload json trace test.', () => {

    cy.visit('https://127.0.0.1:8000/efelg/');

    cy.contains('Next').click({ force: true });
    cy.url().should('include', 'show_traces');

    cy.get('#user_files_1', {timeout: 600000}).selectFile('cypress/fixtures/json_example.json', {'force': true});
    cy.get('#json_extension_1').click({'force': true});
    cy.get('.form-control').should('have.class', 'is-valid');
    cy.get('#upload_button_1').click({ force: true });

    cy.get('#charts_upload_1', {timeout: 60000}).should('be.visible');

    cy.get('.cell_selall', {timeout: 60000}).each(($cell) => {
        cy.wrap($cell).click({force: true});
    }),

    cy.get('#next_checkbox', {timeout: 60000}).click({force: true});
    cy.contains('Next', {timeout: 60000}).should('be.enabled').click({ force: true });

    cy.get('.overlay-content').should('be.visible');
    cy.get('#e-st-user-choice-accept-btn').click({force: true});

    cy.url().should('include', 'select_features');

    cy.get('.span-check', {timeout: 60000}).each(($feature) => {
        var r = Math.random();
        if (r > 0.5) {
            cy.wrap($feature).click({force: true});
        }
    });
    cy.contains('Next').click({ force: true });

    cy.get('#wmd-first').contains('Error').should('not.exist');
    cy.get('.btn.btn-lg.btn-success', { timeout: 600000 }).should('be.enabled');
  });

  it('NFE upload abf trace with .json metadata test.', () => {

    cy.visit(URL);

    cy.contains('Next').click();
    cy.url().should('include', 'show_traces');

    cy.get('#user_files_1', {timeout: 600000}).selectFile(['cypress/fixtures/abf_example.abf', 'cypress/fixtures/abf_example_metadata.json'], {'force': true});
    cy.get('#abf_extension_1').click({'force': true});
    cy.get('.form-control').should('have.class', 'is-valid');
    cy.get('#upload_button_1').click({ force: true });

    cy.get('#charts_upload_1', {timeout: 60000}).should('be.visible');

    cy.get('.cell_selall', {timeout: 60000}).each(($cell) => {
        cy.wrap($cell).click({force: true});
    }),

    cy.get('#next_checkbox', {timeout: 60000}).click({force: true});
    cy.contains('Next', {timeout: 60000}).should('be.enabled').click({ force: true });

    cy.get('.overlay-content').should('be.visible');
    cy.get('#e-st-user-choice-accept-btn').click({force: true});

    cy.url().should('include', 'select_features');

    cy.get('.span-check', {timeout: 60000}).each(($feature) => {
        var r = Math.random();
        if (r > 0.5) {
            cy.wrap($feature).click({force: true});
        }
    });
    cy.contains('Next').click({ force: true });

    cy.get('#wmd-first').contains('Error').should('not.exist');
    cy.get('.btn.btn-lg.btn-success', { timeout: 600000 }).should('be.enabled');
  });

  it('NFE overview page test.', () => {

    cy.visit(URL);

    cy.get('#tutorial_div').should('be.not.visible');
    cy.get('#tutorial_button').click({ force: true });
    cy.get('#tutorial_div').should('be.visible');
    cy.get('#tutorial_button').click({ force: true });
    cy.get('#tutorial_div').should('be.not.visible');

    cy.get('.fas.fa-home').should('be.visible').click({ force: true });
    cy.url({ decode: true }).should('contain', 'overview');

    cy.get('.fas.fa-info-circle').should('be.visible');
    cy.get('.fas.fa-play').should('be.visible');

  });

  it('NFE docs test.', () => {

    cy.visit(URL.concat('docs/'));

    cy.url().should('eq', URL.concat('docs/'));

    cy.get('.text-white.fs-6').contains('Home').click({ force: true });
    cy.url().should('eq', URL.concat('docs/index/'));

    cy.get('.text-white.fs-6').contains('File Format').click({ force: true });
    cy.url().should('eq', URL.concat('docs/file_formats/'));
    cy.contains('abf_example.abf').click({ force: true });
    cy.contains('abf_example_metadata.json').click({ force: true });
    cy.contains('json_example.json').click({ force: true });

    cy.get('.text-white.fs-6').contains('Dataset').click({ force: true });
    cy.url().should('eq', URL.concat('docs/dataset/'));

  });
})

