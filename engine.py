import cv2
import numpy as np
import functools


def change_sharp(img):
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    img = cv2.GaussianBlur(img, (5, 5), 0)
    img = cv2.filter2D(img, -1, kernel)
    return img


def change_constrast(img):
    lookuptable = np.empty((1,256), np.uint8)
    gamma = 3.2
    for i in range(256):
        lookuptable[0,i] = np.clip(pow(i / 255.0, gamma) * 255.0, 0, 255)
    return cv2.LUT(img, lookuptable)


def change_morphology(img):
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
    closed = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
    closed = cv2.dilate(closed, None, iterations=4)
    closed = cv2.erode(closed, None, iterations=2)
    return closed


def get_border(img):
    blurred = cv2.GaussianBlur(img, (9, 9), 0)
    border = cv2.Canny(blurred, 20, 20)
    return border


def remove_holes(img):
    contours, hierarch = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    for i in range(len(contours)):
        if hierarch[0][i][3] != -1:
            cv2.drawContours(img, [contours[i]], 0, 255, -1)
    return img


def read_img(path):
    return cv2.imread(path, cv2.IMREAD_GRAYSCALE)


def simple(path):
    img = read_img(path)
    # cv2.imshow(path+'org', img)
    img = change_sharp(img)
    img = change_constrast(img)
    border = get_border(img)
    mor = change_morphology(border)
    res = remove_holes(mor)
    # cv2.imshow(path, res)
    return res


def get_pixels(img):
    lst = []
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            if img.item(i, j) != 0:
                lst.append((i, j))
    return lst


def encode(img, lst, u, x0):
    T = 16
    m = 10
    j = 8
    H = []
    L = []

    for p in lst:
        v = img.item(p)
        H.append(v // T)
        L.append(v % T)

    x = [x0]
    for i in range(m + len(lst)):
        k = j if i < m else j + L[i - m]
        Gk = 2 ** (k % 7 + 8)
        L_u_xn = u * x[i] * (1 - x[i])
        x.append(L_u_xn * Gk - int(L_u_xn * Gk))
    x = x[m + 1:]

    pos = 100000
    ep = 1e-5
    for i in range(len(lst)):
        intx = int((x[i] - int(x[i])) * pos + ep) % (256 // T)
        nHv = H[i] ^ intx
        img.itemset(lst[i], nHv * T + L[i])

    return img


def decode(img, lst, u, x0):
    return encode(img, lst, u, x0)


def encode_change_pos(img, lst, u, x0):
    T = 16
    m = 10
    j = 8
    H = []
    L = []

    for p in lst:
        v = img.item(p)
        H.append(v // T)
        L.append(v % T)

    x = [(x0, 0)]
    for i in range(m + len(lst)):
        k = j if i < m else j + L[i - m]
        Gk = 2 ** (k % 7 + 8)
        L_u_xn = u * x[i][0] * (1 - x[i][0])
        x.append((L_u_xn * Gk - int(L_u_xn * Gk), i - m))
    x = x[m + 1:]
    x.sort(key=lambda v:v[0])

    pos = 100000
    ep = 1e-5
    for i in range(len(lst)):
        intx = int((x[i][0] - int(x[i][0])) * pos + ep) % (256 // T)
        nHv = H[x[i][1]] ^ intx
        img.itemset(lst[i], nHv * T + L[i])

    return img


def decode_change_pos(img, lst, u, x0):
    T = 16
    m = 10
    j = 8
    H = []
    L = []

    for p in lst:
        v = img.item(p)
        H.append(v // T)
        L.append(v % T)

    x = [(x0, 0)]
    for i in range(m + len(lst)):
        k = j if i < m else j + L[i - m]
        Gk = 2 ** (k % 7 + 8)
        L_u_xn = u * x[i][0] * (1 - x[i][0])
        x.append((L_u_xn * Gk - int(L_u_xn * Gk), i - m))
    x = x[m + 1:]
    x.sort(key=lambda v:v[0])

    pos = 100000
    ep = 1e-5
    for i in range(len(lst)):
        intx = int((x[i][0] - int(x[i][0])) * pos + ep) % (256 // T)
        nHv = H[i] ^ intx
        img.itemset(lst[x[i][1]], nHv * T + L[i])

    return img


def main():
    # imgs = ['mri_head.jpg', 'mri_bone.jpg', 'mri_brain.jpg', 'mri_heart.jpg', 'mri_heart0.jpg']
    # imgs = ['test_1.jpg', 'test_2.jpg']
    imgs = ['small_0.jpg', 'small_1.jpg', 'small_2.jpg', 'small_3.jpg', 'small_4.jpg']
    for img_name in imgs:
        img = simple(img_name)
        cv2.imwrite(img_name[:-4] + '_mask.jpg', img)
        lst = get_pixels(img)
        encoded_img = encode_change_pos(read_img(img_name), lst, 3.0, 0.7123)
        cv2.imwrite(img_name[:-4] + '_encoded.jpg', encoded_img)
        # cv2.imshow(img_name + '_encoded', encoded_img)
        decoded_img = decode_change_pos(encoded_img, lst, 3.0, 0.7123)
        # cv2.imshow(img_name + '_decoded', decoded_img)
        cv2.imwrite(img_name[:-4] + '_decoded.jpg', decoded_img)

    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
