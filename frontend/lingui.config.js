module.exports = {
    locales: ["en", "ru", "de"],
    sourceLocale: "en",
    compileNamespace: "ts",
    catalogs: [
        {
            path: "src/locales/{locale}/messages",
            include: ["src"],
        },
    ],
    format: "po",
};
