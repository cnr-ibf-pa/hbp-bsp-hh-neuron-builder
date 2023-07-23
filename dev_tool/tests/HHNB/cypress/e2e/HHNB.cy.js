// HHNB.spec.js created with Cypress
//
// Start writing your Cypress tests below!
// If you're unfamiliar with how Cypress works,
// check out the link below and learn how to write your first test:
// https://on.cypress.io/writing-first-test


Cypress.on('uncaught:exception', (err) => {
  return false;
})

describe('Hodgkin-Huxley Neuron Builder Automatic Tests', () => {

    const URL = Cypress.env('host').concat('/hh-neuron-builder/');

    beforeEach(() => {
      cy.visit(URL);
      cy.get('#js-banner-block').should('be.visible');
      cy.get('#js-banner-button').click();
      cy.get('#js-banner-block').should('be.not.visible');
      cy.wait(100);
      cy.get('#new-wf').should('be.visible').should('be.enabled').click();
      cy.url().should('include', 'workflow/tab_');

      cy.get('#wf-title').should('contain', 'Workflow ID:');
    });

    /* it('Login tests', () => {
      cy.get('#loginButton').click({ force: true });
      cy.origin('iam.ebrains.eu', () => {
        cy.url().should('include', 'https://iam.ebrains.eu/auth');
        cy.get('input#username', {timeout: 10000}).type(Cypress.env('username'));
        cy.get('input#password').type(Cypress.env('password'));
        cy.get('button#kc-login').click({ force: true });
      })
      cy.get('#loginButton').should('be.not.exist');
      cy.get('.logout').should('be.visible');
      cy.get('.user-img').should('be.visible');
    });
     */
    it('New workflow test', () => {
      const wfTitle = cy.get('#wf-title').invoke('text').then((text) => {
        return text;
      });
      cy.wait(1000);
      cy.get('#wf-btn-new-wf').click();
      cy.get('#wf-title').invoke('text').then(text => {
        expect(text).to.not.equal(wfTitle);
      });
    })

    it('All buttons disabled test.', () => {
      cy.get('.btn-link').should('be.disabled');
      cy.get('#launch-opt-btn').should('be.disabled');
      cy.get('#run-sim-btn').should('be.disabled');
    })

    it('Feature extraction test.', () => {

      // status bar
      cy.get('.status-bar.status-bar-text').should('have.class', 'red');
      cy.get('#feat-bar').should('have.class', 'red').and('has.html', '"features.json" file NOT present<br>"protocols.json" file NOT present');

      cy.get('#modalNFEContainer').should('be.not.visible');
      cy.get('#feat-efel-btn').click();
      cy.get('#modalNFEContainer').should('be.visible');
      cy.get('#save-feature-files').should('be.disabled');
      cy.get('#closeNFEButton').should('be.enabled').click();

      // upload features
      cy.get('#overlayupload').should('exist').and('be.not.visible');
      cy.get('#feat-up-btn').click();
      cy.get('#overlayupload').should('be.visible');
      cy.get('#uploadFormLabel').should('has.html', '<strong>Upload features files ("features.json" and "protocols.json")</strong>');
      cy.get('#uploadFormButton').should('be.disabled');
      cy.get('#cancelUploadFormButton').should('be.enabled').click();
      cy.get('#overlayupload').should('be.not.visible');
      cy.get('#feat-up-btn').click();
      cy.get('#formFile').selectFile(['cypress/fixtures/features.json', 'cypress/fixtures/protocols.json'], {'force': true});
      cy.get('#uploadFormButton').should('be.enabled').click();
      cy.get('#feat-bar').should('has.class', 'green').and('has.text', '');
      cy.get('#feat-efel-btn').should('be.disabled');
      cy.get('#feat-up-btn').should('be.disabled');
      cy.get('#down-feat-btn').should('be.enabled');

      // delete features
      cy.get('#del-feat-btn').should('be.enabled').click();
      cy.get('#feat-bar').should('has.class', 'red').and('has.html', '"features.json" file NOT present<br>"protocols.json" file NOT present');
      cy.get('#feat-up-btn').should('be.enabled');
      cy.get('#feat-efel-btn').should('be.enabled');
      cy.get('#down-feat-btn').should('be.disabled');
      cy.get('#del-feat-btn').should('be.disabled');

    });

    it('Optimization files test.', () => {

      // status bar
      cy.get('#opt-files-bar').should('has.class', 'red').and('has.html', '"morphology" file NOT present<br>"mechanisms" files NOT present<br>"parameters.json" file NOT present');

      // check buttons
      cy.get('#down-opt-set-btn').should('be.disabled');
      cy.get('#del-opt-btn').should('be.disabled');
      cy.get('#opt-db-hpc-btn').should('be.enabled');
      cy.get('#show-opt-files-btn').should('be.enabled');
      cy.get('#opt-up-btn').should('be.enabled');

      // test upload files
      cy.get('#opt-up-btn').click();
      cy.get('#overlayupload').should('be.visible');
      cy.get('#uploadFormLabel').should('has.html', '<strong>Upload optimization settings (".zip")</strong>');
      cy.get('#uploadFormButton').should('be.disabled');
      cy.get('#cancelUploadFormButton').should('be.enabled').click();
      cy.get('#overlayupload').should('be.not.visible');
      cy.get('#opt-up-btn').click();
      cy.get('#overlayupload').should('be.visible');
      cy.get('#formFile').selectFile('cypress/fixtures/orig_model_signed.zip', {'force': true});
      cy.get('#uploadFormButton').should('be.enabled').click();
      cy.get('#overlayupload').should('be.not.visible');

      // check bar and buttons
      cy.get('#opt-files-bar').should('has.class', 'green').and('has.text', '');
      cy.get('#down-opt-set-btn').should('be.enabled');
      cy.get('#del-opt-btn').should('be.enabled');
      cy.get('#opt-db-hpc-btn').should('be.disabled');
      cy.get('#show-opt-files-btn').should('be.enabled');
      cy.get('#opt-up-btn').should('be.disabled');

    });

    it('Optimization files manager test.', () => {

      // status bar
      cy.get('#opt-files-bar').should('has.class', 'red').and('has.html', '"morphology" file NOT present<br>"mechanisms" files NOT present<br>"parameters.json" file NOT present');

      // check buttons
      cy.get('#down-opt-set-btn').should('be.disabled');
      cy.get('#del-opt-btn').should('be.disabled');
      cy.get('#opt-db-hpc-btn').should('be.enabled');
      cy.get('#show-opt-files-btn').should('be.enabled');
      cy.get('#opt-up-btn').should('be.enabled');

      // test file manager
      cy.get('#filemanager').should('be.not.visible');
      cy.get('#show-opt-files-btn').should('be.visible').click();
      cy.get('#filemanager').should('be.visible');

      // check folders and content
      cy.get('#morphologyFolder').click();
      cy.get('#morphologyFileList').find('.file-item').should('has.class', 'empty');
      cy.get('#refreshFileListButton').should('has.not.class', 'disabled');
      cy.get('#selectAllButton').should('has.class', 'disabled');
      cy.get('#downloadFileButton').should('has.class', 'disabled');
      cy.get('#uploadFileButton').should('has.not.class', 'disabled');
      cy.get('#deleteFileButton').should('has.class', 'disabled');
      cy.get('#editFileButton').should('be.not.visible');

      cy.get('#mechanismsFolder').click();
      cy.get('#mechanismsFileList').find('.file-item').should('has.class', 'empty');
      cy.get('#refreshFileListButton').should('has.not.class', 'disabled');
      cy.get('#selectAllButton').should('has.class', 'disabled');
      cy.get('#downloadFileButton').should('has.class', 'disabled');
      cy.get('#uploadFileButton').should('has.not.class', 'disabled');
      cy.get('#deleteFileButton').should('has.class', 'disabled');
      cy.get('#editFileButton').should('be.not.visible');

      cy.get('#configFolder').click();
      cy.get('#configFileList').find('.file-item').should('has.class', 'empty');
      cy.get('#refreshFileListButton').should('has.not.class', 'disabled');
      cy.get('#selectAllButton').should('has.class', 'disabled');
      cy.get('#downloadFileButton').should('has.class', 'disabled');
      cy.get('#uploadFileButton').should('has.not.class', 'disabled');
      cy.get('#deleteFileButton').should('has.class', 'disabled');
      cy.get('#editFileButton').should('be.visible');

      cy.get('#modelFolder').click();
      cy.get('#modelFileList').find('.file-item').should('has.not.class', 'empty');
      cy.get('#modelFileList').contains('analysis.py');
      cy.get('#modelFileList').contains('__init__.py');
      cy.get('#modelFileList').contains('template.py');
      cy.get('#modelFileList').contains('evaluator.py');
      cy.get('#refreshFileListButton').should('has.not.class', 'disabled');
      cy.get('#selectAllButton').should('has.not.class', 'disabled');
      cy.get('#downloadFileButton').should('has.not.class', 'disabled');
      cy.get('#uploadFileButton').should('has.class', 'disabled');
      cy.get('#deleteFileButton').should('has.class', 'disabled');
      cy.get('#editFileButton').should('be.visible');

      cy.get('#optNeuronFolder').click();
      cy.get('#optNeuronTextArea').should('be.visible');
    })

    it('Optimization settings test.', () => {

      // status bar
      cy.get('#opt-param-bar').should('has.html', 'Optimization parameters NOT set');
      cy.get('#overlayparam').should('be.not.visible');
      cy.get('#opt-set-btn').should('be.enabled').click();
      cy.get('.loading-animation').should('be.visible');
      cy.get('#overlayparam').should('be.visible');

      // check buttons
      cy.get('#cancel-param-btn').should('be.enabled');
      cy.get('#apply-param').should('be.disabled');
      cy.get('.accordion-button.hpc').should('be.enabled').and('have.not.class', 'active');

      // check accordions
      cy.get('.accordion-collapse[data-bs-parent="#hpcChooserParams"]').should('be.not.visible');

      // test accordion Daint
      cy.get('#accordionDaint').click().should('has.class', 'active');
      cy.get('#accordionNSG').should('has.not.class', 'active');
      cy.get('#accordionSA').should('has.not.class', 'active');

      cy.get('#daintCollapse').should('be.visible');
      cy.get('#apply-param').should('be.enabled');
      cy.wait(300);
      cy.get('#accordionDaint').click().should('has.not.class', 'active');
      cy.get('#apply-param').should('be.disabled');

      // test accordion NSG
      cy.get('#accordionNSG').click().should('has.class', 'active');
      cy.get('#accordionDaint').should('has.not.class', 'active');
      cy.get('#accordionSA').should('has.not.class', 'active');

      cy.get('#nsgCollapse').should('be.visible');
      cy.get('#apply-param').should('be.enabled');
      cy.wait(300);
      cy.get('#accordionNSG').click().should('has.not.class', 'active');
      cy.get('#apply-param').should('be.disabled');

      // test accordion SA
      cy.get('#accordionSA').click().should('has.class', 'active');
      cy.get('#accordionNSG').should('has.not.class', 'active');
      cy.get('#accordionDaint').should('has.not.class', 'active');

      cy.get('#saCollapse').should('be.visible');
      cy.get('#apply-param').should('be.enabled');
      cy.wait(300);
      cy.get('#accordionSA').click().should('has.not.class', 'active');
      cy.get('#apply-param').should('be.disabled');


      // test switch accordion
      cy.get('.accordion-collapse[data-bs-parent="#hpcChooserParams"]').should('be.not.visible');
      cy.get('#accordionSA').click().should('has.class', 'active');
      cy.get('#saCollapse').should('be.visible');
      cy.wait(300);
      cy.get('#accordionNSG').click().should('has.class', 'active');
      cy.get('#accordionSA').should('has.not.class', 'active');
      cy.get('#nsgCollapse').should('be.visible');
      cy.get('#saCollapse').should('be.not.visible');
      cy.wait(300);
      cy.get('#accordionDaint').click().should('has.class', 'active');
      cy.get('#accordionNSG').should('has.not.class', 'active');
      cy.get('#daintCollapse').should('be.visible');
      cy.get('#nsgCollapse').should('be.not.visible');

      cy.get('#apply-param').should('be.enabled').click();
      cy.get('#alert.alert-warning').should('be.visible').and('has.text', 'Please fill "Project ID" to apply settings and continue your workflow.');
      cy.get('#alert-button').should('be.visible').click();
      cy.wait(300);
      cy.get('#daint_project_id').should('has.class', 'is-invalid').type('test');
      cy.get('#apply-param').should('be.enabled').click();
      cy.get('#alert.alert-warning').should('be.visible').and('has.text', 'You need to be logged in to use this HPC system !Please, click "Cancel" and login with the button in the top right corner before doing this operation.');
      cy.get('#alert-button').should('be.visible').click();
      cy.wait(300);

      cy.get('#accordionNSG').click();
      cy.get('#nsgCollapse').should('be.visible');
      cy.get('#apply-param').should('be.enabled').click();
      cy.get('#alert.alert-warning').should('be.visible').and('has.text', 'Please fill "username" and/or "password" to apply settings and continue your workflow.');
      cy.get('#alert-button').should('be.visible').click();
      cy.get('#username_submit').should('has.class', 'is-invalid');
      cy.get('#password_submit').should('has.class', 'is-invalid');

      cy.wait(300);
      cy.get('#accordionSA').click();
      cy.get('#saCollapse').should('be.visible');
      cy.get('#sa-project-dropdown-optset-btn').should('be.disabled');
      cy.get('#sa-hpc-dropdown-optset-btn').should('be.enabled').click();
      cy.get('.sa-dropdown-menu').should('be.visible');
      cy.get('a#dropdown-item-hpc-nsg').click();
      cy.get('#sa-project-dropdown-optset-btn').should('be.enabled');
    })

    it('Single cell run optimization upload NSG result test.', () =>{

      // test bar and buttons
      cy.get('#opt-param-bar').should('has.html', 'Optimization parameters NOT set');
      cy.get('#opt-res-bar').should('has.html', 'Fetch job results or upload a previously downloaded "zip" to run analysis');

      cy.get('#opt-fetch-btn').should('be.enabled');
      cy.get('#opt-res-up-btn').should('be.enabled');

      cy.get('#show-results-btn').should('be.disabled');
      cy.get('#down-opt-btn').should('be.disabled');
      cy.get('#down-sim-btn').should('be.disabled');
      cy.get('#del-sim-btn').should('be.disabled');

      cy.get('#overlayjobs').should('be.not.visible');
      cy.get('#opt-fetch-btn').click();
      cy.get('#overlayjobs').should('be.visible');
      cy.get('#refresh-job-list-btn').should('be.disabled');
      cy.get('#cancel-job-list-btn').should('be.enabled').click();

      // upload NSG results
      cy.get('#overlayupload').should('be.not.visible');
      cy.get('#opt-res-up-btn').click();
      cy.get('#overlayupload').should('be.visible');
      cy.get('#cancelUploadFormButton').should('be.enabled');
      cy.get('#uploadFormButton').should('be.disabled');
      cy.get('#uploadFormLabel').should('has.html', '<strong>Upload model (".zip")</strong>');
      cy.get('input#formFile').selectFile('cypress/fixtures/nsg_results_signed.zip', {'force': true});
      cy.get('#uploadFormButton').should('be.enabled').click();
      cy.get('#overlayupload').should('be.not.visible');
      cy.get('.loading-animation').should('be.visible');
      cy.get('.loading-animation', { timeout: 60000 }).should('be.not.visible');
      cy.get('#opt-fetch-btn').should('be.disabled');
      cy.get('#opt-res-up-btn').should('be.disabled');
      cy.get('#show-results-btn').should('be.enabled');
      cy.get('#down-opt-btn').should('be.enabled');
      cy.get('#down-sim-btn').should('be.enabled');
      cy.get('#del-sim-btn').should('be.enabled');
      cy.get('#run-sim-btn').should('be.enabled');

      // upload to bluenaas
      cy.get('#modalBlueNaas').should('be.not.visible');
      cy.get('#run-sim-btn').should('be.enabled').click();
      cy.get('.loading-animation').should('be.visible');
      cy.get('.loading-animation', { timeout: 60000 }).should('be.not.visible');
      cy.get('#modalBlueNaas').should('be.visible');
      cy.get('#reload-bluenaas').should('be.enabled');
      cy.get('#reg-mod-main-btn').should('be.enabled');

      cy.get('#back-to-wf-btn').should('be.enabled').click();
      cy.get('#modalBlueNaas').should('be.not.visible');

      cy.get('#run-sim-btn').click();
      cy.get('#modalBlueNaas').should('be.visible');
      cy.get('#reload-bluenaas').click();
      cy.get('#reload-bluenaas').should('be.disabled');
      cy.get('#reload-bluenaas', { timeout: 60000 }).should('be.enabled');

      cy.get('#reg-mod-main-btn').click();
      cy.get('#overlaywrapmodreg').should('be.not.visible');
      cy.get('#modalBlueNaas').should('be.not.visible');
      cy.get('.loading-animation').should('be.visible');
      cy.get('.loading-animation', { timeout: 60000 }).should('be.not.visible');
      cy.get('#overlaywrapmodreg').should('be.visible');
      cy.get('#cancel-model-register-btn').should('be.enabled');
      cy.get('#register-model-btn').should('be.enabled').click();
      cy.get('.loading-animation').should('be.visible');
      cy.get('#alert-dialog.alert.alert-danger', { timeout: 60000 }).should('be.visible');
      cy.get('.alert-dialog-button').should('be.enabled').click();
      cy.get('#alert-dialog.alert.alert-danger').should('be.not.exist');
      cy.get('#cancel-model-register-btn').click();
      cy.get('#overlaywrapmodreg').should('be.not.visible');
      cy.get('#modalBlueNaas').should('be.visible');
      cy.get('#back-to-wf-btn').should('be.enabled').click();
      cy.get('#modalBlueNaas').should('be.not.visible');

      // delete
      cy.get('#del-sim-btn').click();
      cy.get('#opt-param-bar').should('has.html', 'Optimization parameters NOT set');
      cy.get('#opt-res-bar').should('has.html', 'Fetch job results or upload a previously downloaded "zip" to run analysis');

      cy.get('#opt-fetch-btn').should('be.enabled');
      cy.get('#opt-res-up-btn').should('be.enabled');

      cy.get('#show-results-btn').should('be.disabled');
      cy.get('#down-opt-btn').should('be.disabled');
      cy.get('#down-sim-btn').should('be.disabled');
      cy.get('#del-sim-btn').should('be.disabled');

      cy.get('#overlayjobs').should('be.not.visible');
      cy.get('#opt-fetch-btn').click();
      cy.get('#overlayjobs').should('be.visible');
      cy.get('#refresh-job-list-btn').should('be.disabled');
      cy.get('#cancel-job-list-btn').should('be.enabled').click();
    });

    it('Single cell run optimization upload NSG analysis test.', () =>{

      // test bar and buttons
      cy.get('#opt-param-bar').should('has.html', 'Optimization parameters NOT set');
      cy.get('#opt-res-bar').should('has.html', 'Fetch job results or upload a previously downloaded "zip" to run analysis');

      cy.get('#opt-fetch-btn').should('be.enabled');
      cy.get('#opt-res-up-btn').should('be.enabled');

      cy.get('#show-results-btn').should('be.disabled');
      cy.get('#down-opt-btn').should('be.disabled');
      cy.get('#down-sim-btn').should('be.disabled');
      cy.get('#del-sim-btn').should('be.disabled');

      cy.get('#overlayjobs').should('be.not.visible');
      cy.get('#opt-fetch-btn').click();
      cy.get('#overlayjobs').should('be.visible');
      cy.get('#refresh-job-list-btn').should('be.disabled');
      cy.get('#cancel-job-list-btn').should('be.enabled').click();

      // upload NSG analysis
      cy.get('#overlayupload').should('be.not.visible');
      cy.get('#opt-res-up-btn').click();
      cy.get('#overlayupload').should('be.visible');
      cy.get('#cancelUploadFormButton').should('be.enabled');
      cy.get('#uploadFormButton').should('be.disabled');
      cy.get('#uploadFormLabel').should('has.html', '<strong>Upload model (".zip")</strong>');
      cy.get('input#formFile').selectFile('cypress/fixtures/nsg_analysis_signed.zip', {'force': true});
      cy.get('#uploadFormButton').should('be.enabled').click();
      cy.get('#overlayupload').should('be.not.visible');
      cy.wait(500);
      cy.get('.loading-animation', { timeout: 60000 }).should('be.not.visible');
      cy.get('#opt-fetch-btn').should('be.disabled');
      cy.get('#opt-res-up-btn').should('be.disabled');
      cy.get('#show-results-btn').should('be.enabled');
      cy.get('#down-opt-btn').should('be.disabled');
      cy.get('#down-sim-btn').should('be.enabled');
      cy.get('#del-sim-btn').should('be.enabled');

      // upload to bluenaas
      cy.get('#modalBlueNaas').should('be.not.visible');
      cy.get('#run-sim-btn').should('be.enabled').click();
      cy.get('.loading-animation').should('be.visible');
      cy.get('.loading-animation', { timeout: 60000 }).should('be.not.visible');

      cy.get('#modalBlueNaas').should('be.visible');
      cy.get('#reload-bluenaas').should('be.enabled');
      cy.get('#reg-mod-main-btn').should('be.enabled');

      cy.get('#back-to-wf-btn').should('be.enabled').click();
      cy.get('#modalBlueNaas').should('be.not.visible');

      cy.get('#run-sim-btn').click();
      cy.get('#modalBlueNaas').should('be.visible');
      cy.get('#reload-bluenaas').click();
      cy.get('#reload-bluenaas').should('be.disabled');
      cy.get('#reload-bluenaas', { timeout: 60000 }).should('be.enabled');

      cy.get('#reg-mod-main-btn').click();
      cy.get('#overlaywrapmodreg').should('be.not.visible');
      cy.get('#modalBlueNaas').should('be.not.visible');
      cy.get('.loading-animation').should('be.visible');
      cy.get('.loading-animation', { timeout: 60000 }).should('be.not.visible');
      cy.get('#overlaywrapmodreg').should('be.visible');
      cy.get('#cancel-model-register-btn').should('be.enabled');
      cy.get('#register-model-btn').should('be.enabled').click();
      cy.get('.loading-animation').should('be.visible');
      cy.get('#alert-dialog.alert.alert-danger', { timeout: 60000 }).should('be.visible');
      cy.get('.alert-dialog-button').should('be.enabled').click();
      cy.get('#alert-dialog.alert.alert-danger').should('be.not.exist');
      cy.get('#cancel-model-register-btn').click();
      cy.get('#overlaywrapmodreg').should('be.not.visible');
      cy.get('#modalBlueNaas').should('be.visible');
      cy.get('#back-to-wf-btn').should('be.enabled').click();
      cy.get('#modalBlueNaas').should('be.not.visible');

      // delete
      cy.get('#del-sim-btn').click();
      cy.get('#opt-param-bar').should('has.html', 'Optimization parameters NOT set');
      cy.get('#opt-res-bar').should('has.html', 'Fetch job results or upload a previously downloaded "zip" to run analysis');

      cy.get('#opt-fetch-btn').should('be.enabled');
      cy.get('#opt-res-up-btn').should('be.enabled');

      cy.get('#show-results-btn').should('be.disabled');
      cy.get('#down-opt-btn').should('be.disabled');
      cy.get('#down-sim-btn').should('be.disabled');
      cy.get('#del-sim-btn').should('be.disabled');

      cy.get('#overlayjobs').should('be.not.visible');
      cy.get('#opt-fetch-btn').click();
      cy.get('#overlayjobs').should('be.visible');
      cy.get('#refresh-job-list-btn').should('be.disabled');
      cy.get('#cancel-job-list-btn').should('be.enabled').click();
    });

    it('Single cell run optimization upload DAINT result test.', () =>{

      // test bar and buttons
      cy.get('#opt-param-bar').should('has.html', 'Optimization parameters NOT set');
      cy.get('#opt-res-bar').should('has.html', 'Fetch job results or upload a previously downloaded "zip" to run analysis');

      cy.get('#opt-fetch-btn').should('be.enabled');
      cy.get('#opt-res-up-btn').should('be.enabled');

      cy.get('#show-results-btn').should('be.disabled');
      cy.get('#down-opt-btn').should('be.disabled');
      cy.get('#down-sim-btn').should('be.disabled');
      cy.get('#del-sim-btn').should('be.disabled');

      cy.get('#overlayjobs').should('be.not.visible');
      cy.get('#opt-fetch-btn').click();
      cy.get('#overlayjobs').should('be.visible');
      cy.get('#refresh-job-list-btn').should('be.disabled');
      cy.get('#cancel-job-list-btn').should('be.enabled').click();

      // upload DAINT results
      cy.get('#overlayupload').should('be.not.visible');
      cy.get('#opt-res-up-btn').click();
      cy.get('#overlayupload').should('be.visible');
      cy.get('#cancelUploadFormButton').should('be.enabled');
      cy.get('#uploadFormButton').should('be.disabled');
      cy.get('#uploadFormLabel').should('has.html', '<strong>Upload model (".zip")</strong>');
      cy.get('input#formFile').selectFile('cypress/fixtures/daint_results_signed.zip', {'force': true});
      cy.get('#uploadFormButton').should('be.enabled').click();
      cy.get('#overlayupload').should('be.not.visible');
      cy.get('.loading-animation').should('be.visible');
      cy.get('.loading-animation', { timeout: 60000 }).should('be.not.visible');
      cy.get('#opt-fetch-btn').should('be.disabled');
      cy.get('#opt-res-up-btn').should('be.disabled');
      cy.get('#show-results-btn').should('be.enabled');
      cy.get('#down-opt-btn').should('be.enabled');
      cy.get('#down-sim-btn').should('be.enabled');
      cy.get('#del-sim-btn').should('be.enabled');
      cy.get('#run-sim-btn').should('be.enabled');

      // upload to bluenaas
      cy.get('#modalBlueNaas').should('be.not.visible');
      cy.get('#run-sim-btn').should('be.enabled').click();
      cy.get('.loading-animation').should('be.visible');
      cy.get('.loading-animation', { timeout: 60000 }).should('be.not.visible');
      cy.get('#modalBlueNaas').should('be.visible');
      cy.get('#reload-bluenaas').should('be.enabled');
      cy.get('#reg-mod-main-btn').should('be.enabled');

      cy.get('#back-to-wf-btn').should('be.enabled').click();
      cy.get('#modalBlueNaas').should('be.not.visible');

      cy.get('#run-sim-btn').click();
      cy.get('#modalBlueNaas').should('be.visible');
      cy.get('#reload-bluenaas').click();
      cy.get('#reload-bluenaas').should('be.disabled');
      cy.get('#reload-bluenaas', { timeout: 60000 }).should('be.enabled');

      cy.get('#reg-mod-main-btn').click();
      cy.get('#overlaywrapmodreg').should('be.not.visible');
      cy.get('#modalBlueNaas').should('be.not.visible');
      cy.get('.loading-animation').should('be.visible');
      cy.get('.loading-animation', { timeout: 60000 }).should('be.not.visible');
      cy.get('#overlaywrapmodreg').should('be.visible');
      cy.get('#cancel-model-register-btn').should('be.enabled');
      cy.get('#register-model-btn').should('be.enabled').click();
      cy.get('.loading-animation').should('be.visible');
      cy.get('#alert-dialog.alert.alert-danger', { timeout: 60000 }).should('be.visible');
      cy.get('.alert-dialog-button').should('be.enabled').click();
      cy.get('#alert-dialog.alert.alert-danger').should('be.not.exist');
      cy.get('#cancel-model-register-btn').click();
      cy.get('#overlaywrapmodreg').should('be.not.visible');
      cy.get('#modalBlueNaas').should('be.visible');
      cy.get('#back-to-wf-btn').should('be.enabled').click();
      cy.get('#modalBlueNaas').should('be.not.visible');

      // delete
      cy.get('#del-sim-btn').click();
      cy.get('#opt-param-bar').should('has.html', 'Optimization parameters NOT set');
      cy.get('#opt-res-bar').should('has.html', 'Fetch job results or upload a previously downloaded "zip" to run analysis');

      cy.get('#opt-fetch-btn').should('be.enabled');
      cy.get('#opt-res-up-btn').should('be.enabled');

      cy.get('#show-results-btn').should('be.disabled');
      cy.get('#down-opt-btn').should('be.disabled');
      cy.get('#down-sim-btn').should('be.disabled');
      cy.get('#del-sim-btn').should('be.disabled');

      cy.get('#overlayjobs').should('be.not.visible');
      cy.get('#opt-fetch-btn').click();
      cy.get('#overlayjobs').should('be.visible');
      cy.get('#refresh-job-list-btn').should('be.disabled');
      cy.get('#cancel-job-list-btn').should('be.enabled').click();
    });

    it('Single cell run optimization upload DAINT analysis test.', () =>{

      // test bar and buttons
      cy.get('#opt-param-bar').should('has.html', 'Optimization parameters NOT set');
      cy.get('#opt-res-bar').should('has.html', 'Fetch job results or upload a previously downloaded "zip" to run analysis');

      cy.get('#opt-fetch-btn').should('be.enabled');
      cy.get('#opt-res-up-btn').should('be.enabled');

      cy.get('#show-results-btn').should('be.disabled');
      cy.get('#down-opt-btn').should('be.disabled');
      cy.get('#down-sim-btn').should('be.disabled');
      cy.get('#del-sim-btn').should('be.disabled');

      cy.get('#overlayjobs').should('be.not.visible');
      cy.get('#opt-fetch-btn').click();
      cy.get('#overlayjobs').should('be.visible');
      cy.get('#refresh-job-list-btn').should('be.disabled');
      cy.get('#cancel-job-list-btn').should('be.enabled').click();

      // upload DAINT analysis
      cy.get('#overlayupload').should('be.not.visible');
      cy.get('#opt-res-up-btn').click();
      cy.get('#overlayupload').should('be.visible');
      cy.get('#cancelUploadFormButton').should('be.enabled');
      cy.get('#uploadFormButton').should('be.disabled');
      cy.get('#uploadFormLabel').should('has.html', '<strong>Upload model (".zip")</strong>');
      cy.get('input#formFile').selectFile('cypress/fixtures/daint_analysis_signed.zip', {'force': true});
      cy.get('#uploadFormButton').should('be.enabled').click();
      cy.get('#overlayupload').should('be.not.visible');
      cy.wait(500);
      cy.get('.loading-animation', { timeout: 60000 }).should('be.not.visible');
      cy.get('#opt-fetch-btn').should('be.disabled');
      cy.get('#opt-res-up-btn').should('be.disabled');
      cy.get('#show-results-btn').should('be.enabled');
      cy.get('#down-opt-btn').should('be.disabled');
      cy.get('#down-sim-btn').should('be.enabled');
      cy.get('#del-sim-btn').should('be.enabled');

      // upload to bluenaas
      cy.get('#modalBlueNaas').should('be.not.visible');
      cy.get('#run-sim-btn').should('be.enabled').click();
      cy.get('.loading-animation').should('be.visible');
      cy.get('.loading-animation', { timeout: 60000 }).should('be.not.visible');
      cy.get('#modalBlueNaas').should('be.visible');
      cy.get('#reload-bluenaas').should('be.enabled');
      cy.get('#reg-mod-main-btn').should('be.enabled');

      cy.get('#back-to-wf-btn').should('be.enabled').click();
      cy.get('#modalBlueNaas').should('be.not.visible');

      cy.get('#run-sim-btn').click();
      cy.get('#modalBlueNaas').should('be.visible');
      cy.get('#reload-bluenaas').click();
      cy.get('#reload-bluenaas').should('be.disabled');
      cy.get('#reload-bluenaas', { timeout: 60000 }).should('be.enabled');

      cy.get('#reg-mod-main-btn').click();
      cy.get('#overlaywrapmodreg').should('be.not.visible');
      cy.get('#modalBlueNaas').should('be.not.visible');
      cy.get('.loading-animation').should('be.visible');
      cy.get('.loading-animation', { timeout: 60000 }).should('be.not.visible');
      cy.get('#overlaywrapmodreg').should('be.visible');
      cy.get('#cancel-model-register-btn').should('be.enabled');
      cy.get('#register-model-btn').should('be.enabled').click();
      cy.get('.loading-animation').should('be.visible');
      cy.get('#alert-dialog.alert.alert-danger', { timeout: 60000 }).should('be.visible');
      cy.get('.alert-dialog-button').should('be.enabled').click();
      cy.get('#alert-dialog.alert.alert-danger').should('be.not.exist');
      cy.get('#cancel-model-register-btn').click();
      cy.get('#overlaywrapmodreg').should('be.not.visible');
      cy.get('#modalBlueNaas').should('be.visible');
      cy.get('#back-to-wf-btn').should('be.enabled').click();
      cy.get('#modalBlueNaas').should('be.not.visible');

      // delete
      cy.get('#del-sim-btn').click();
      cy.get('#opt-param-bar').should('has.html', 'Optimization parameters NOT set');
      cy.get('#opt-res-bar').should('has.html', 'Fetch job results or upload a previously downloaded "zip" to run analysis');

      cy.get('#opt-fetch-btn').should('be.enabled');
      cy.get('#opt-res-up-btn').should('be.enabled');

      cy.get('#show-results-btn').should('be.disabled');
      cy.get('#down-opt-btn').should('be.disabled');
      cy.get('#down-sim-btn').should('be.disabled');
      cy.get('#del-sim-btn').should('be.disabled');

      cy.get('#overlayjobs').should('be.not.visible');
      cy.get('#opt-fetch-btn').click();
      cy.get('#overlayjobs').should('be.visible');
      cy.get('#refresh-job-list-btn').should('be.disabled');
      cy.get('#cancel-job-list-btn').should('be.enabled').click();
    });
  });

