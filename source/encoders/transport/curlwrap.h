#ifndef __CURL_WRAP_H_
#define __CURL_WRAP_H_

#include <curl/curl.h>

#include <exception>
#include <string>

class curl_exception : std::exception {
public:
    explicit curl_exception(CURLcode code_) : code(code_) {}
    const char *what() const noexcept override {
        return curl_easy_strerror(code);
    }

private:
    CURLcode code;
};

class CurlWrap {
public:
    CurlWrap() {
        curl = curl_easy_init();
        form = NULL;
        if (!curl) {
            throw curl_exception(CURLE_FAILED_INIT);
        }
    }
    ~CurlWrap() {
        if (curl) {
            curl_easy_cleanup(curl);
            if (form != NULL) {
                curl_mime_free(form);
            }
        }
    }

    template <class T>
    void setopt(CURLoption option, T parameter) {
        CURLcode res = curl_easy_setopt(curl, option, parameter);
        if (res != CURLE_OK) {
            throw curl_exception(res);
        }
    }
    template <class T>
    T getinfo(CURLINFO info) {
        T result;
        CURLcode res = curl_easy_getinfo(curl, info, &result);
        if (res != CURLE_OK) {
            throw curl_exception(res);
        }
        return result;
    }
    void perform() {
        CURLcode res = curl_easy_perform(curl);
        if (res != CURLE_OK) {
            throw curl_exception(res);
        }
    }

    void createUploadForm(std::string &filePath) {
        // Create the form
        form = curl_mime_init(curl);

        curl_mimepart *field = NULL;

        // Fill in the file upload field
        field = curl_mime_addpart(form);
        curl_mime_name(field, "file");
        curl_mime_filedata(field, filePath.c_str());

        curl_easy_setopt(curl, CURLOPT_MIMEPOST, form);
    }

    // Allows instances to be implicitly converted to
    // the underlying pointer for using the API directly
    operator CURL *() {
        return curl;
    }

    // Disable copying or moving
    CurlWrap(const CurlWrap &) = delete;
    CurlWrap &operator=(const CurlWrap &) = delete;
    CurlWrap(CurlWrap &&) = delete;
    CurlWrap &operator=(CurlWrap &&) = delete;

private:
    CURL *curl;
    curl_mime *form;
};

#endif
