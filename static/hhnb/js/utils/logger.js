export default class Log {

    static enabled = false;

    static debug(msg) {
        if (this.enabled) {
            console.log(msg);
        }
    }

    static info(msg) {
        if (this.enabled) {
            console.info(msg);
        }
    }

    static warning(msg) {
        if (this.enabled) {
            console.warn(msg);
        }
    }

    static error(msg) {
        if (this.enabled) {
            console.error(msg);
        }
    }
}