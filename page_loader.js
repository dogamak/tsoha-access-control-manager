const path = require('path');

module.exports = function (source) {
    const relative = path.relative(this.context, this.resourcePath);

    return `
        import { init } from '../../bootstrap.js';
        import PageComponent from './${path.basename(this.resourcePath)}';

        import '../../../css/base.scss';

        init(PageComponent);
    `;
};