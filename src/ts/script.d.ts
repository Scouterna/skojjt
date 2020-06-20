declare namespace ScoutId {
    interface loginResponse {
        user: number | false;
        admin: boolean;
    }

    interface jwtBadResponse {
        ok: false;
        error: string;
        url: string;
    }
    interface jwtGoodResponse {
        ok: true;
        token: string;
    }
    type jwtResponse = jwtGoodResponse|jwtBadResponse;

    interface stringObject {
        [key: string]: string;
    }

    interface jwtData {
        iss: string;
        sub: string;
        exp: number;
        iat: number;
        name: string;
        email: string;
        dob: string;
        role: string[];
        karer: stringObject;
    }
    interface whoamiResponse {
        user: string|false;
        admin: boolean;
        data: jwtData;
        error?: string;
    }
}
